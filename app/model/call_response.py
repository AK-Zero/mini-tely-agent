from pydantic import BaseModel

class CallResponse(BaseModel):
    call_id: str
    room_name: str
    status: str
    message: str