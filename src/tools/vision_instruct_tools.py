# Convert Image to Text
from typing import Dict, Any
import base64
import json
from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.oci_genai_vision import initialize_llm
from src.data.sales_order import Transaction as data_structure
import os
from pathlib import Path

@tool(description_mode="only_docstring")
def image_to_text_tool(query: str) -> str:
    """Tool that is invoked for a image .jpg file detailing the order, and returns the tool name.

    Parameters
    ----------
    query:
        file type

    Returns
        -------
        tool name

    """
    return "image_to_text_tool"

# Load and encode your image (local file)
def encode_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded

def image_to_text(image_path:str, question:str) -> str:

    # Encode image
    image_base64 = encode_image_as_base64(image_path)

    data_schema_str = json.dumps(data_structure.model_json_schema(), indent=2)

    # Construct message with image and text
    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": f"{question}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        ),
        SystemMessage(
            "You are a helpful assistant. Use the schema below to extract structured JSON from the user's request.\n"
            "Respond with valid JSON inside triple backticks like ```json ... ```.\n\n"
            "Schema:\n```json\n{data_schema_str}\n```"
            "Return only the Final json, and nothing else"
            )
    ]

    llm = initialize_llm()
    # print(messages)
    response = llm.invoke(messages)
    #print(response.content)
    return response.content

def test_image_to_text() -> str:
    THIS_DIR = Path(__file__).resolve()
    PROJECT_ROOT = THIS_DIR.parent.parent.parent

    image_path = f"{PROJECT_ROOT}/order_inputs/orderhub_handwritten.jpg"
    question = ("""Get all information about the order such as - 
BillToCustomer - Name {}, BusinessUnit {}
OrderItems - Item: {}, Quantity: {}, RequestedDate: {}
"""
                )
    # print(image_path)
    response = image_to_text(image_path, question)
    return response

if __name__ == "__main__":
    response = test_image_to_text()
    print(response)