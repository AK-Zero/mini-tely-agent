from pydantic import BaseModel

class PersonaSpec(BaseModel):
    name: str
    persona_prompt: str