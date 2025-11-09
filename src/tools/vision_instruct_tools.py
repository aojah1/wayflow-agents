# --- imports minimal ---
import base64, json
from pathlib import Path

from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.oci_genai_vision import initialize_llm_vision
from src.llm.oci_genai_structured_output import initialize_llm_so
from src.data.sales_order import Transaction

# ---------- tiny utility (not a JSON helper) ----------
def _encode_image_as_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# ---------- tool wrapper ----------
@tool(description_mode="only_docstring")
def image_to_text(file_path: str, question: str) -> str:
    """
    Convert an order image to structured JSON using a vision LLM,
    then normalize with a structured LLM (Transaction schema).
    Always returns a JSON string.
    """
    return image_to_text_impl(file_path, question)

def image_to_text_impl(file_path: str, question: str) -> str:
    """
    Fast path:
    1) Vision LLM: produce structured text (it may include extra prose).
    2) Structured LLM: normalize to Transaction and emit ONLY JSON.
    3) Return JSON string (no heavy helper logic).
    """
    # 1) Vision call
    image_b64 = _encode_image_as_base64(file_path)
    vision_msgs = [
        SystemMessage(
            content=(
                """
                "Extract all order information with this schema:\n"
                "BillToCustomer - Name, BusinessUnit \n"
                "OrderItems - Item: {}, Quantity: {}, RequestedDate: {}\n"
                "Return only JSON."
                "If BusinessUnit is empty, than replace by 'US-1 Business Unit'"
                """
            )
        ),
        HumanMessage(
            content=[
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ]
        ),
    ]
    vision_llm = initialize_llm_vision()
    vision_resp = vision_llm.invoke(vision_msgs)
    #vision_text = str(getattr(vision_resp, "content", vision_resp))

    # 2) Structured normalization (no local JSON parsing)
    so_llm = initialize_llm_so().with_structured_output(Transaction)
    normalized = so_llm.invoke(vision_resp.content)

    # 3) Return as JSON string (minimal conversion only)
    if isinstance(normalized, (dict, list)):
        return json.dumps(normalized, ensure_ascii=False)
    # Some SDKs return BaseModel-like objects; try model_dump if present, else str
    dump_fn = getattr(normalized, "model_dump", None)
    if callable(dump_fn):
        return json.dumps(dump_fn(), ensure_ascii=False)
    return str(normalized)

# ---------- quick test ----------
def test():
    from src.llm.oci_genai import initialize_llm
    _ = initialize_llm()  # not used here; keeps parity with your previous test

    assistant = Agent(
        custom_instruction="Get information from the file",
        tools=[image_to_text],
        llm=_,  # placeholder if your Agent requires an llm; otherwise remove
    )

    THIS_DIR = Path(__file__).resolve()
    PROJECT_ROOT = THIS_DIR.parent.parent.parent
    file_path = f"{PROJECT_ROOT}/order_inputs/orderhub_handwritten.jpg"
    question = (
        "Extract all order information \n"
        "Return only JSON."
    )

    # Direct call (deterministic)
    print(image_to_text_impl(file_path=file_path, question=question))

    # Wayflow conversation path (optional)
    convo = assistant.start_conversation()
    convo.append_user_message(f"file_path: {file_path}\nquestion: {question}")
    convo.execute()
    ans = convo.get_last_message()
    print(ans.content)

if __name__ == "__main__":
    test()
