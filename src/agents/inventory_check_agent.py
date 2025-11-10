from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.tools.aidp_fdi_inventory_check_tools import aidp_fdi_inventory_check

import re
from typing import List, Dict, Any

def inventory_check_agent(user_msg: str):

    llm = initialize_llm()

    assistant = Agent(
        custom_instruction="Check item inventory for the provided list of item_numbers, list of item_required_quantity, and bu. Respond ONLY JSON with proper line breaks",
        tools=[aidp_fdi_inventory_check], 
        llm=llm
    )

    conversation = assistant.start_conversation()
    #user_msg = f"item_numbers: {item_numbers}\nitem_required_quantity: {item_required_quantity}\nbu: {bu}\nquestion: {question}"
    conversation.append_user_message(user_msg)
    status = conversation.execute()

    if isinstance(status, UserMessageRequestStatus):
        assistant_reply = conversation.get_last_message()
    else:
        assistant_reply = f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}"
        print(f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}")

    return assistant_reply.content

def unit_test():
    item_numbers = ['AS6647431', 'AS6647432', 'AS6647433']
    item_required_quantity = [2000, 1000, 5000]
    bu = "US1 Business Unit"
    user_msg = f"Return per-item availability for item_numbers: {item_numbers}, item_required_quantity: {item_required_quantity} and bu: {bu}"
    response = inventory_check_agent(user_msg)
    print(f"Agent Output : {response}" )



if __name__ == "__main__":
    unit_test()