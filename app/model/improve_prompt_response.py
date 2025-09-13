from pydantic import BaseModel
from typing import List, Dict, Any

class ImprovePromptResponse(BaseModel):
    run_id: str
    transcripts: List[List[Dict[str, str]]]
    metrics: List[Dict[str, Any]]
    improved_prompts: List[str]
    final_improved_prompt: str