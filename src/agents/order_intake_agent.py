
from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.system_prompts.order_intake_agent_prompts import prompt_order_intake_agent
from src.tools.vision_instruct_tools import image_to_text
from src.tools.speech_instruct_tools import voice_to_text
import os
from pathlib import Path

def order_intake():

    llm = initialize_llm()

    # order_intake_agent_instructions = prompt_order_intake_agent.strip()

    assistant = Agent(
        custom_instruction="Get information from the file",
        tools=[voice_to_text, image_to_text], 
        llm=llm
    )    

    THIS_DIR = Path(__file__).resolve()
    PROJECT_ROOT = THIS_DIR.parent.parent.parent
    file_path = f"{PROJECT_ROOT}/order_inputs/orderhub_handwritten.jpg"
    question = (
        "Extract all order information with this schema:\n"
        "BillToCustomer - Name, BusinessUnit \n"
        "OrderItems - Item: {}, Quantity: {}, RequestedDate: {}\n"
        "Return only JSON."
    )

    conversation = assistant.start_conversation()
    user_msg = f"file_path: {file_path}\nquestion: {question}"
    conversation.append_user_message(user_msg)
    conversation.execute()

    assistant_response = conversation.get_last_message()
    print(assistant_response.content)

if __name__ == "__main__":
    order_intake()
