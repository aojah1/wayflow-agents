
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

    SQL_PATH = f"{PROJECT_ROOT}/config/inventory_check2.sql"

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
        # cursor.execute("SELECT count(*) FROM fdi_idl_catalog.default.dw_internal_org_d")
        # cursor.execute("SELECT count(*) FROM fdi_idl_catalog.default.dw_inventory_item_d")
        with open(SQL_PATH, "r") as f:
            sql_script = f.read()
        for statement in sql_script.split(';'):
            if statement.strip(): # Avoid empty statements
                # cursor.execute(statement)
                item_number = "AS6647431"
                cursor.execute(sql_script, (item_number,))
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
