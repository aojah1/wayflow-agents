from langchain_oci import ChatOCIGenAI
from pydantic import BaseModel

class Joke(BaseModel):
    setup: str
    punchline: str

from src.common.config import *

# print(f"AUTH_TYPE: {AUTH_TYPE}")
# print(f"MODEL_ID: {MODEL_ID}")
# print(f"ENDPOINT: {ENDPOINT}")
# print(f"COMPARTMENT_ID: {COMPARTMENT_ID}")


def initialize_llm_so():
    try:
        return ChatOCIGenAI(
            model_id=MODEL_ID,
            service_endpoint=ENDPOINT,
            compartment_id=COMPARTMENT_ID,
            provider=PROVIDER,
            model_kwargs={
                "temperature": 0.5,
                "max_tokens": 512,
                # remove any unsupported kwargs like citation_types
            },
            auth_type=AUTH_TYPE,
        )
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        raise
def unit_test():
    llm = initialize_llm_so()
    structured_llm = llm.with_structured_output(Joke)
    print(structured_llm.invoke("Tell me a joke about programming"))

if __name__ == "__main__":
    unit_test()