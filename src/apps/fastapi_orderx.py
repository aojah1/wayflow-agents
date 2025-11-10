from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Dict
import shutil
from src.agents.inventory_check_agent import inventory_check_agent
from src.agents.order_intake_agent import order_intake_agent
from src.agents.order_create_agent import order_create_agent
import traceback, json, os

app = FastAPI()

@app.post("/orders/image")
async def ask_agent_from_image(
    image: UploadFile = File(...),
    question: str = Form(...)
):
    try:
        # Save image locally
        temp_path = Path("/tmp") / image.filename
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)


        # Build the prompt
        input_prompt = f"{str(temp_path)}   \n{question}"
        response = order_intake_agent(input_prompt)
        #response = await agent_image2text.run_async(input_prompt, max_steps=5)
        print(response)

    
        return JSONResponse(content={"final_answer": response})

    except Exception as e:
        # Print the full stack trace to stdout/logs
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )


@app.get("/orders/inventory")
async def check_inventory(input_prompt: str):
    try:
        response = inventory_check_agent(input_prompt)
        print(response)

        return JSONResponse(content={"final_answer": response})
    except Exception as e:
        # Print the full stack trace to stdout/logs
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

@app.post("/orders/create")
async def create_sales_order(payload: Dict = Body(...)):
    """
    Create an order using the OCI AI agent and a structured JSON payload.
    """
    try:
        # Convert the Python dict to a properly escaped JSON string
        payload_json = json.dumps(payload)

        # Construct a human-readable prompt with embedded JSON
        input_prompt = f"Create a sales order using a properly structured JSON payload:\n{payload_json}"

        response = order_create_agent(input_prompt)
        print(response)

        return JSONResponse(content={"final_answer": response})
    except Exception as e:
        # Print the full stack trace to stdout/logs
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
    

from pydantic import BaseModel, EmailStr
import traceback, json
# --- models ---
class SalesEmailRequest(BaseModel):
    saas_transaction_id: str | int
    email_to: EmailStr = "ops@example.com"
    subject: str | None = None           # optional; we’ll default if missing
    final_message: str | None = None     # prefer this for the body
    note: str | None = None              # fallback for body


@app.post("/orders/email")
async def email_sales_order(payload: SalesEmailRequest):
    """
    Email the status of the Sales Order to a CSR via create_order_agent's email tool.
    """
    try:
        subject = payload.subject or f"Sales Order Status for orderid: {payload.saas_transaction_id}"
        # prefer final_message; fallback to note; final fallback generic line
        body = (
            payload.final_message
            or payload.note
            or f"Status update for order {payload.saas_transaction_id}."
        )

        # Build the exact string your agent expects
        input_prompt = (
            "send an email -\n"
            f"to: {payload.email_to}\n"
            f"subject: {subject}\n"
            f"body: {body}"
        )

        response = order_create_agent(input_prompt)
        return JSONResponse(content={"final_answer": response})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )