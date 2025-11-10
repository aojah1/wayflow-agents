# src/tools/aidp_inventory_check_tool.py
import os
from multiprocessing import Process, Queue
from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from wayflowcore.executors.executionstatus import UserMessageRequestStatus
from typing import List

from src.common.config import (
    PROJECT_ROOT, JDBC_DRIVER_CLASS_NAME, JDBC_URL, AUTH_TYPE,
    OCI_CONFIG_FILE, CONFIG_PROFILE
)

# ---------- child worker (runs JPype + JDBC in separate process) ----------
def _jdbc_worker(item_numbers: List[str], item_required_quantities: List[int], bu: str, q) -> None:
    """
    item_numbers: list[str]
    item_required_quantities: list[int]  (same length as item_numbers)
    bu: str
    q: multiprocessing.Queue  -> puts a list[dict] or 'Error: ...'
    """
    import os, json
    import jpype, jaydebeapi

    try:
        # validate inputs
        if not isinstance(item_numbers, (list, tuple)) or not item_numbers:
            q.put("Error: item_numbers must be a non-empty list")
            return
        if not isinstance(item_required_quantities, (list, tuple)) or \
           len(item_required_quantities) != len(item_numbers):
            q.put("Error: item_required_quantity must be a list with same length as item_numbers")
            return
        if not isinstance(bu, str) or not bu.strip():
            q.put("Error: bu must be a non-empty string")
            return

        # locate jar(s)
        JAR_CANDIDATES = [
            os.path.join(PROJECT_ROOT, "config", "SparkJDBC42.jar"),
            os.path.join(PROJECT_ROOT, "config", "SimbaSparkJDBC42.jar"),
        ]
        jars = [p for p in JAR_CANDIDATES if os.path.isfile(p)]
        if not jars:
            q.put("Error: JDBC jar not found at expected locations: " + ", ".join(JAR_CANDIDATES))
            return

        # start JVM with explicit classpath
        if not jpype.isJVMStarted():
            jpype.startJVM(convertStrings=True, classpath=jars)

        # sanity check driver
        DRIVER_CLASS = "com.simba.spark.jdbc.Driver"
        try:
            _ = jpype.JClass(DRIVER_CLASS)
        except Exception as e:
            q.put(f"Error: Driver class '{DRIVER_CLASS}' not found on classpath ({os.pathsep.join(jars)}): {e}")
            return

        # connect
        props = {
            "oracle.jdbc.authenticationMethod": AUTH_TYPE,
            "oracle.jdbc.oci.config.file": OCI_CONFIG_FILE,
            "oracle.jdbc.oci.profile.name": CONFIG_PROFILE,
        }
        conn = jaydebeapi.connect(DRIVER_CLASS, JDBC_URL, props, jars)

        try:
            cur = conn.cursor()
            sql_path = os.path.join(PROJECT_ROOT, "config", "inventory_check3.sql")
            if not os.path.isfile(sql_path):
                q.put(f"Error: SQL file not found: {sql_path}")
                return

            sql_template = open(sql_path, "r").read()

            # Build IN list placeholders and finalize SQL.
            # SQL file must contain:  ... item.item_number IN ({items}) ... AND bu.business_unit_name = ?
            placeholders = ", ".join(["?"] * len(item_numbers))
            if "{items}" not in sql_template:
                q.put("Error: SQL template must contain a {items} token for the IN list")
                return
            sql = sql_template.format(items=placeholders)

            # Params: all item_numbers first (for IN list), then BU (for the trailing '?')
            params = tuple(item_numbers) + (bu,)

            cur.execute(sql, params)
            rows = cur.fetchall()
        finally:
            try: cur.close()
            except Exception: pass
            try: conn.close()
            except Exception: pass

        # rows expected as: (available_quantity, item_number, org_code, org_id, subinv, bu_name)
        # Build a map for quick lookup by item_number
        qty_by_item = {}
        for r in rows or []:
            try:
                qty_by_item[str(r[1])] = int(r[0]) if r[0] is not None else 0
            except Exception:
                # fallback if types are odd
                qty_by_item[str(r[1])] = int(float(r[0])) if r and r[0] is not None else 0

        result = []
        for i, it in enumerate(item_numbers):
            available = qty_by_item.get(str(it), 0)
            required = int(item_required_quantities[i])
            result.append({
                "item_number": str(it),
                "available_quantity": int(available),
                "required_quantity": required,
                "is_available": "Yes" if available >= required else "No",
                "business_unit": bu
            })

        q.put(json.dumps(result))  # return JSON string (Wayflow tools usually return str)

    except Exception as e:
        q.put(f"Error: {e}")
    finally:
        try:
            if jpype.isJVMStarted():
                jpype.shutdownJVM()
        except Exception:
            pass


# ---------- tool wrapper (calls child process, then kills it) ----------
@tool(description_mode="only_docstring")
def aidp_fdi_inventory_check(
    item_numbers: List[str],
    item_required_quantity: List[int],
    bu: str,
    question: str,
) -> str:
    """
    Check item availability in FDI using AIDP for a LIST of item_numbers.
    Returns a JSON array with:
      [{ "item_number": "...", "available_quantity": int, "required_quantity": int, "is_available": "Yes|No", "business_unit": "..." }, ...]
    """
    q = Queue()
    p = Process(target=_jdbc_worker, args=(item_numbers, item_required_quantity, bu, q), daemon=False)
    p.start()
    p.join(timeout=60)

    if p.is_alive():
        p.terminate()
        p.join(5)

    try:
        return q.get_nowait()
    except Exception:
        return "Error: JDBC worker timed out"



# ---------- quick test ----------
def test():
    from src.llm.oci_genai import initialize_llm
    llm = initialize_llm()

    assistant = Agent(
        custom_instruction="Check item inventory",
        tools=[aidp_fdi_inventory_check],
        llm=llm
    )

    item_numbers = ['AS6647431', 'AS6647432', 'AS6647433']
    item_required_quantity = [2000, 1000, 5000]
    bu = "US1 Business Unit"
    question = "Return per-item availability."

    convo = assistant.start_conversation()
    # Keep the user message explicit so the agent/tool router has zero ambiguity
    user_msg = (
        f"aidp_fdi_inventory_check(item_numbers={item_numbers}, "
        f"item_required_quantity={item_required_quantity}, bu='{bu}', question='{question}')"
    )
    convo.append_user_message(user_msg)
    status = convo.execute()

    print("Final Output")
    if isinstance(status, UserMessageRequestStatus):
        print(f"---\nResult >>> {convo.get_last_message().content}\n---")
    else:
        print(f"---\nResult >>> {convo.get_last_message().content}\n---")

if __name__ == "__main__":
    test()
