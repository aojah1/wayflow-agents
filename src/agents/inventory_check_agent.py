
from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool
from wayflowcore.models import OCIGenAIModel
from src.llm.oci_genai import initialize_llm
from src.tools.aidp_fdi_inventory_check_tools import aidp_fdi_inventory_check

def inventory_check():

    llm = initialize_llm()

    assistant = Agent(
        custom_instruction="Check item inventory",
        tools=[aidp_fdi_inventory_check], 
        llm=llm
    )

    item_number = "AS6647431"
    item_required_quantity = 9000
    bu = "US1 Business Unit"   
    question = (
        "Check the available_quantity returned by the tool\n"
        "If available_quantity is more than item_required_quantity, then respond Yes \n"
        "If available_quantity is less than item_required_quantity, then respond No \n"
        "Return only Yes or No \n"
    )   

    print(f"--------\nItem Number >>> {item_number}\n--------")
    print(f"--------\nQuantity requested >>> {item_required_quantity}\n--------")

    # print(aidp_fdi_inventory_check_impl(item_number=item_number, item_required_quantity=item_required_quantity, bu=bu, question=question)) 

    conversation = assistant.start_conversation()
    user_msg = f"item_number: {item_number}\nitem_required_quantity: {item_required_quantity}\nbu: {bu}\nquestion: {question}"
    conversation.append_user_message(user_msg)
    status = conversation.execute()

    print("Agent Output")

    if isinstance(status, UserMessageRequestStatus):
        assistant_reply = conversation.get_last_message()
        print(f"---\nAIDP Inventory Available? >>> {assistant_reply.content}\n---")
    else:
        print(f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}")

if __name__ == "__main__":
    inventory_check()
