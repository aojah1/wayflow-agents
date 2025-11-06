
from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.tools.order_create_tools import create_order

import re
from typing import List, Dict, Any

def order_create_intake(user_msg: str):

    llm = initialize_llm()

    assistant = Agent(
        custom_instruction="Create Order in Fusion. Respond ONLY JSON with proper line breaks",
        tools=[create_order],
        llm=llm
    )

    # Test Payload
    payload = {
        "title": "foo",
        "body": "bar",
        "userId": 1,
    }

    conversation = assistant.start_conversation()
    conversation.append_user_message(user_msg)
    status = conversation.execute()

    if isinstance(status, UserMessageRequestStatus):
        assistant_reply = conversation.get_last_message()
    else:
        assistant_reply = f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}"
        print(f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}")

    return assistant_reply.content

def unit_test():
    # Test Payload
    payload = {
        "title": "foo",
        "body": "bar",
        "userId": 1,
    }
    user_msg = f"payload: {payload}"
    response = order_create_intake(user_msg)
    print(f"Agent Output : {response}")

if __name__ == "__main__":
    unit_test()