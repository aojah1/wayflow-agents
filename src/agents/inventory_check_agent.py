
from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.common.config import *
import os
import jaydebeapi
import jpype

def inventory_check():

    JDBC_DRIVER_PATH = f"{PROJECT_ROOT}/config/SparkJDBC42.jar"

    SQL_PATH = f"{PROJECT_ROOT}/config/inventory_check3.sql"

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
        item_number = "AS6647431"
        bu = "US1 Business Unit"
        parameters = [
            (item_number, bu)
        ]
        cursor.execute(sql_script, parameters[0])
        results = cursor.fetchall()
        print("AIDP Output")
        print(results)

    except jaydebeapi.Error as e:
        print(f"Error connecting to database: {e}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    inventory_check()
