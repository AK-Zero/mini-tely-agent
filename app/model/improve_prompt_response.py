from pydantic import BaseModel
from typing import List, Dict, Any

class ImprovePromptResponse(BaseModel):
    run_id: str
    transcript: List[Dict[str, str]]
    metrics: Dict[str, Any]
    improved_prompt: str