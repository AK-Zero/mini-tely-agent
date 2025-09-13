from pydantic import BaseModel
from typing import Optional, List
from .persona_spec import PersonaSpec

class ImprovePromptRequestAuto(BaseModel):
    base_agent_prompt: str
    persona_names: List[str]
    max_turns: Optional[int] = 8