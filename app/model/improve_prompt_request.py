from pydantic import BaseModel
from typing import Optional
from .persona_spec import PersonaSpec

class ImprovePromptRequest(BaseModel):
    base_agent_prompt: str
    persona: PersonaSpec
    max_turns: Optional[int] = 8