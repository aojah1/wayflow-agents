
from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.system_prompts.order_intake_agent_prompts import prompt_order_intake_agent
from src.tools.vision_instruct_tools import image_to_text
from src.tools.speech_instruct_tools import voice_to_text
import os
from pathlib import Path

def order_intake_agent(user_msg: str):

    llm = initialize_llm()

    # order_intake_agent_instructions = prompt_order_intake_agent.strip()

    assistant = Agent(
        custom_instruction="Get information from the file",
        tools=[voice_to_text, image_to_text], 
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
    THIS_DIR = Path(__file__).resolve()
    PROJECT_ROOT = THIS_DIR.parent.parent.parent
    file_path = f"{PROJECT_ROOT}/order_inputs/orderhub_handwritten.jpg"
    question = (
        "Extract all order information with this schema:\n"
        "BillToCustomer - Name, BusinessUnit \n"
        "OrderItems - Item: {}, Quantity: {}, RequestedDate: {}\n"
        "Return only JSON."
    )
    user_msg = f"file_path: {file_path}\nquestion: {question}"
    
    response = order_intake_agent(user_msg)
    print(f"---\nAgent Output : {response}\n---" )


if __name__ == "__main__":
    unit_test()
