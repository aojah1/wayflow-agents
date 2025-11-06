import json
import requests

from wayflowcore.agent import Agent
from wayflowcore.tools import tool
from wayflowcore.executors.executionstatus import UserMessageRequestStatus

from src.llm.oci_genai_vision import initialize_llm_vision
from src.common.config import *

# ---------- tool wrapper ----------
@tool(description_mode="only_docstring")
def create_order(payload: str) -> str:
    """
    a tool to create order in Fusion
    :param payload str:
    :return: Fusion JSON string response
    """
    return create_order_impl(payload)

def create_order_impl(payload: str) -> str:
    """Plain callable that actually does the work."""
    try:

        headers = {
            "Content-Type": "application/vnd.oracle.adf.resourceitem+json",
            "Accept": "application/vnd.oracle.adf.resourceitem+json"
            # "Authorization": f"Bearer {bearer_token}"
        }

        payload = json.dumps(payload)

        response = requests.post(
            API_URL,
            headers=headers,
            data=payload
        )

        response.raise_for_status()
 
    except requests.exceptions.RequestException as e:
        return f"API call failed: {str(e)}" 

    return f"Response: {response.json()}"

'''

def test_create_sales_order():

    payload = {
      "SourceTransactionNumber": "R210_Sample_Order_ATOModel_227",
      "SourceTransactionSystem": "OPS",
      "SourceTransactionId": "R210_Sample_Order_ATOModel_227",
      "TransactionalCurrencyCode": "USD",
      "BusinessUnitId": 300000046987012,
      "BuyingPartyNumber": "10060",
      "TransactionTypeCode": "STD",
      "RequestedShipDate": "2018-09-19T19:51:48+00:00",
      "SubmittedFlag": "true",
      "FreezePriceFlag": "false",
      "FreezeShippingChargeFlag": "false",
      "FreezeTaxFlag": "false",
      "RequestingBusinessUnitId": 300000046987012,
      "lines": [
        {
          "SourceTransactionLineId": "1",
          "SourceTransactionLineNumber": "1",
          "SourceScheduleNumber": "1",
          "SourceTransactionScheduleId": "1",
          "OrderedUOMCode": "zzu",
          "OrderedQuantity": 10,
          "ProductNumber": "AS6647431",
          "FOBPoint": "Destination",
          "FreightTerms": "Add freight",
          "PaymentTerms": "30 Net",
          "ShipmentPriority": "High"
        },
        {
          "SourceTransactionLineId": "2",
          "SourceTransactionLineNumber": "2",
          "SourceScheduleNumber": "1",
          "SourceTransactionScheduleId": "1",
          "OrderedUOMCode": "zzu",
          "OrderedQuantity": 5,
          "ProductNumber": "AS6647432",
          "FOBPoint": "Destination",
          "FreightTerms": "Add freight",
          "PaymentTerms": "30 Net",
          "ShipmentPriority": "High"
        },
        {
          "SourceTransactionLineId": "3",
          "SourceTransactionLineNumber": "3",
          "SourceScheduleNumber": "1",
          "SourceTransactionScheduleId": "1",
          "OrderedUOMCode": "zzu",
          "OrderedQuantity": 15,
          "ProductNumber": "AS6647433",
          "FOBPoint": "Destination",
          "FreightTerms": "Add freight",
          "PaymentTerms": "30 Net",
          "ShipmentPriority": "High"
        }
      ]
    }

    payload = {
      "BillToCustomer": {
        "Name": "Computer Service and Rentals",
        "BusinessUnit": "US1 Business Unit"
      },
      "OrderItems": [
        {
          "Item": "AS6647431",
          "Quantity": 1,
          "RequestedDate": "5-Nov-25"
        },
        {
          "Item": "AS6647432",
          "Quantity": 1,
          "RequestedDate": "5-Nov-25"
        },
        {
          "Item": "AS6647433",
          "Quantity": 1,
          "RequestedDate": "5-Nov-25"
        }
      ]
    }

'''

# ---------- test / demo ----------
def test():
    from src.llm.oci_genai import initialize_llm
    base_llm = initialize_llm()

    assistant = Agent(
        custom_instruction="Create Order in Fusion. Respond ONLY JSON with proper line breaks",
        tools=[create_order],
        llm=base_llm,
    )

    # Test Payload
    payload = {
        "title": "foo",
        "body": "bar",
        "userId": 1,
    }

    # Deterministic, direct
    # print(create_order_impl(payload=payload))

    # Wayflow conversation path - Non Deterministic Testing
    convo = assistant.start_conversation()
    # Provide input in a form your template can key on
    user_msg = f"payload: {payload}"
    convo.append_user_message(user_msg)
    status = convo.execute()

    if isinstance(status, UserMessageRequestStatus):
        print(f"---\nFusion Order Status >>> \n {convo.get_last_message().content}\n---")
    else:
        assistant_reply = f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}"
        print(f"Invalid execution status, expected UserMessageRequestStatus, received {type(status)}")

if __name__ == "__main__":
    test()
