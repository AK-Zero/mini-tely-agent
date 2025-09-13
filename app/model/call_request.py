from pydantic import BaseModel

class CallRequest(BaseModel):
    phone_number: str
    customer_name: str 
    amount_due: float
    card_number_ending: str 
    agent_instructions: str = None  # Optional custom instructions