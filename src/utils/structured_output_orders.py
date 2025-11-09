from langchain_oci import ChatOCIGenAI
from pydantic import BaseModel
from src.llm.oci_genai_structured_output import initialize_llm_so
from src.data.sales_order import *


llm = initialize_llm_so()
structured_llm = llm.with_structured_output(Transaction)

query = """
BillToCustomer : 111000 
ShipToCustomer: 10124 Louisville
- Item: STOVE-ATO-Model, Quantity: 1, Requested Date: 20-JUL-25
- Item: GAS-FUEL, Quantity: 1, Requested Date: 20-JUL-25
- Item: BURNER-4-GRID, Quantity: 1, Requested Date: 20-JUL-25
"""

print(structured_llm.invoke(query))