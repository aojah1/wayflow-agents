# Convert Voice to Text
from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
import os
import jaydebeapi
import jpype
from src.common.config import *

# ---------- tool wrapper ----------
@tool(description_mode="only_docstring")
def aidp_fdi_inventory_check(item_number: str, item_required_quantity: int, bu: str, question: str) -> str:
    """
    a tool to check item availability in FDI using AIDP
    :param item_number:
    :param item_required_quantity:
    :param bu:
    :param question:
    :return: Required Quantity Available - Yes or No
    """
    return aidp_fdi_inventory_check_impl(item_number, item_required_quantity, bu, question)

def aidp_fdi_inventory_check_impl(item_number: str, item_required_quantity: int, bu: str, question: str) -> str:
    JDBC_DRIVER_PATH = f"{PROJECT_ROOT}/config/SparkJDBC42.jar"

    SQL_PATH = f"{PROJECT_ROOT}/config/inventory_check3.sql"

    print(item_number)

    print(item_required_quantity)

    print(bu)

    print(question)

    connection_properties = {
        "oracle.jdbc.authenticationMethod": AUTH_TYPE, 
        "oracle.jdbc.oci.config.file": OCI_CONFIG_FILE,
        "oracle.jdbc.oci.profile.name": CONFIG_PROFILE
    }

    try:

        conn = jaydebeapi.connect(
            JDBC_DRIVER_CLASS_NAME,
            JDBC_URL,
            connection_properties, 
            JDBC_DRIVER_PATH
        )

        cursor = conn.cursor()

        # Execute SQL queries
        with open(SQL_PATH, "r") as f:
            sql_script = f.read()
        parameters = [
            (item_number, bu)
        ]
        cursor.execute(sql_script, parameters[0])
        results = cursor.fetchall()
        print("Tool Output")
        print(results)

    except jaydebeapi.Error as e:
        print(f"Error connecting to database: {e}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

    return results

# ---------- test / demo ----------
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
        print(f"---\nAIDP Inventory Check Tool >>> {assistant_reply.content}\n---")
    else:
        print(f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}")

if __name__ == "__main__":
    test()