
from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.tools.order_create_tools import create_order
from src.tools.email_tool import send_email_dummy

def order_create_agent(user_msg: str):

    llm = initialize_llm()

    system_prompt = """
    Create Order in Fusion. Respond ONLY JSON with proper line breaks. 
    Now send an email out using the email tool after the create_order_tool comes back with a resppnse (either valid or error).
        f"to: ops@example.com",
        f"subject : Order has been created",
        f"body: Order has been created. The body should be the response form the order_create_tools",
    """
    assistant = Agent(
        custom_instruction="",
        tools=[create_order, send_email_dummy],
        llm=llm
    )

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

    user_msg = f"Create a sales order in Oracle SCM using a properly structured JSON payload.: /n   {payload}"
    response = order_create_agent(user_msg)
    print(f"Agent Output : {response}")

    # send email 

    payload1 = """{
        "action": "send_email",
        "email_to": "ops@example.com",
        "subject": "Order has been created",
        "note": "Order has been created for item_numbers AS6647431, AS6647432."
    }"""
    user_msg1 = f"Send an Email following instructions in this payload /n   {payload1}"
    
    print(user_msg1)
    response1 = order_create_agent(user_msg1)
    print(f"Agent Output Email: {response1}")


if __name__ == "__main__":
    unit_test()