# src/tools/aidp_inventory_check_tool.py
import os
from multiprocessing import Process, Queue, set_start_method
from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)



# ---------- your config ----------
from src.common.config import (
    PROJECT_ROOT, JDBC_DRIVER_CLASS_NAME, JDBC_URL, AUTH_TYPE,
    OCI_CONFIG_FILE, CONFIG_PROFILE
)

# ---------- child worker (runs JPype + JDBC in separate process) ----------
def _jdbc_worker(item_number: str, item_required_quantity: int, bu: str, q):
    """
    Child process that does the JDBC call. Returns 'Yes'/'No' or 'Error: ...' via Queue.
    """
    import os, sys
    import jpype
    import jaydebeapi

    try:
        # 1) Resolve absolute jar path(s)
        #    Name may be 'SparkJDBC42.jar' or 'SimbaSparkJDBC42.jar' – use what you actually have.
        JAR_CANDIDATES = [
            os.path.join(PROJECT_ROOT, "config", "SparkJDBC42.jar"),
            os.path.join(PROJECT_ROOT, "config", "SimbaSparkJDBC42.jar"),
        ]
        jars = [p for p in JAR_CANDIDATES if os.path.isfile(p)]
        if not jars:
            q.put("Error: JDBC jar not found at expected locations: " + ", ".join(JAR_CANDIDATES))
            return

        # 2) Start JVM with explicit classpath
        if not jpype.isJVMStarted():
            # Use classpath=[...] so JPype builds -Djava.class.path for you
            jpype.startJVM(convertStrings=True, classpath=jars)

        # 3) Sanity check: can we load the driver class?
        #    Simba driver class is usually exactly this:
        DRIVER_CLASS = "com.simba.spark.jdbc.Driver"
        try:
            _ = jpype.JClass(DRIVER_CLASS)
        except Exception as e:
            q.put(f"Error: Driver class '{DRIVER_CLASS}' not found on classpath. "
                  f"Classpath={os.pathsep.join(jars)}. Detail: {e}")
            return

        # 4) Open connection
        props = {
            "oracle.jdbc.authenticationMethod": AUTH_TYPE,
            "oracle.jdbc.oci.config.file": OCI_CONFIG_FILE,
            "oracle.jdbc.oci.profile.name": CONFIG_PROFILE,
        }

        # With JVM classpath set, the 'jars' arg is optional, but harmless if you include it.
        conn = jaydebeapi.connect(DRIVER_CLASS, JDBC_URL, props, jars)

        try:
            cur = conn.cursor()
            sql_path = os.path.join(PROJECT_ROOT, "config", "inventory_check3.sql")
            if not os.path.isfile(sql_path):
                q.put(f"Error: SQL file not found: {sql_path}")
                return

            with open(sql_path, "r") as f:
                sql_script = f.read()

            # Bind params as a tuple
            cur.execute(sql_script, (item_number, bu))
            rows = cur.fetchall()
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

        available = int(rows[0][0]) if rows and rows[0] and rows[0][0] is not None else 0
        q.put("Yes" if available >= int(item_required_quantity) else "No")

    except Exception as e:
        q.put(f"Error: {e}")
    finally:
        # We still terminate the child process from the parent,
        # but shutting down here is harmless if it succeeded.
        try:
            if jpype.isJVMStarted():
                jpype.shutdownJVM()
        except Exception:
            pass


# ---------- tool wrapper (calls child process, then kills it) ----------
@tool(description_mode="only_docstring")
def aidp_fdi_inventory_check(item_number: str, item_required_quantity: int, bu: str, question: str) -> str:
    """
    Check item availability in FDI using AIDP.
    Returns ONLY 'Yes' or 'No'.
    """
    q = Queue()
    p = Process(target=_jdbc_worker, args=(item_number, item_required_quantity, bu, q), daemon=False)
    p.start()
    p.join(timeout=30)  # adjust if your query is slower

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

    item_number = "AS6647431"
    item_required_quantity = 2000
    bu = "US1 Business Unit"   
    question = (
        "Check the available_quantity returned by the tool\n"
        "If available_quantity is more than item_required_quantity, then respond Yes \n"
        "If available_quantity is less than item_required_quantity, then respond No \n"
        "Return only Yes or No \n"
    )   

    # print(aidp_fdi_inventory_check_impl(item_number=item_number, item_required_quantity=item_required_quantity, bu=bu, question=question)) 

    convo = assistant.start_conversation()
    user_msg = f"item_number: {item_number}\nitem_required_quantity: {item_required_quantity}\nbu: {bu}\nquestion: {question}"
    convo.append_user_message(user_msg)
    status = convo.execute()

    print("Final Output")

    if isinstance(status, UserMessageRequestStatus):
        assistant_reply = convo.get_last_message()
        print(f"---\nAIDP Inventory Available? >>> {assistant_reply.content}\n---")
    else:
        print(f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}")

if __name__ == "__main__":
    test()
