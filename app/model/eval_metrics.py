from pydantic import BaseModel
from typing import List

class EvalMetrics(BaseModel):
    """Evaluation metrics for conversation analysis"""
    resolution_score: int
    compliance_score: int
    empathy_score: int
    persuasion_score: int
    objections_handled: int
    recommended_prompt_edits: List[str]
    notes: str