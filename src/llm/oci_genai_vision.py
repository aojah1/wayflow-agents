import os
from pathlib import Path
# ─── OCI LLM ──────────────────────────────────────────
from langchain_oci import ChatOCIGenAI
from dotenv import load_dotenv
import base64
from langchain_core.messages import HumanMessage
from src.common.config import *

def initialize_llm_vision():
    return ChatOCIGenAI(
        model_id=MODEL_ID_VISION,
        service_endpoint=ENDPOINT,
        compartment_id=COMPARTMENT_ID,
        provider=PROVIDER,
        model_kwargs={
            "temperature": 1,
            "max_tokens": 600,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "top_p": 0.75
        },
        auth_type=AUTH_TYPE,
        auth_profile=CONFIG_PROFILE,
    )

# Load and encode your image (local file)
def encode_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded

def test():
    
    # Image file and question
    image_path = f"{PROJECT_ROOT}/order_inputs/orderhub_handwritten.jpg"
    question = "What is happening in this image?"

    # Encode image
    image_base64 = encode_image_as_base64(image_path)

    # Construct message with image and text
    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": "What is happening in this image?"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        )
    ]

    llm = initialize_llm_vision()
    response = llm.invoke(messages)
    print(response.content)

if __name__ == "__main__":
    test()