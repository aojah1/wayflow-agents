import os
from pathlib import Path
# ─── OCI LLM ──────────────────────────────────────────
from wayflowcore.models import OCIGenAIModel
from wayflowcore.agent import Agent
from src.common.config import *

print(f"AUTH_TYPE: {AUTH_TYPE}")
print(f"MODEL_ID: {MODEL_ID}")
print(f"ENDPOINT: {ENDPOINT}")
print(f"COMPARTMENT_ID: {COMPARTMENT_ID}")


def initialize_llm():
    try:
        return OCIGenAIModel(
            model_id=MODEL_ID,
            service_endpoint=ENDPOINT,
            compartment_id=COMPARTMENT_ID,
            auth_type=AUTH_TYPE
        )
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        raise




def test():

    llm = initialize_llm()

    assistant = Agent(llm=llm)

    conversation = assistant.start_conversation()
    conversation.append_user_message("What is the capital of Greece")
    conversation.execute()

    # get the assistant's response to your query
    assistant_answer = conversation.get_last_message()
    assistant_answer.content

    print(assistant_answer.content)

if __name__ == "__main__":
    test()