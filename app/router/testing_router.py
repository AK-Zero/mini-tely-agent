import uuid
import logging
from fastapi import APIRouter

from ..service.testing_service import TestingService
from ..model.improve_prompt_request import ImprovePromptRequest
from ..model.improve_prompt_response import ImprovePromptResponse

router = APIRouter(
    prefix="/testing",
    tags=["testing"],
)

logger = logging.getLogger("testing-router")
logging.basicConfig(level=logging.INFO)

testing_service = TestingService()

@router.post("/improve/prompt", response_model=ImprovePromptResponse)
async def improve_prompt(req: ImprovePromptRequest):
    run_id = str(uuid.uuid4())

    transcript = await testing_service.run_simulation(req.base_agent_prompt, req.persona.persona_prompt, req.max_turns)
    metrics = await testing_service.evaluate_conversation(transcript)
    improved_prompt = await testing_service.rewrite_prompt_text(req.base_agent_prompt, metrics.get('recommended_prompt_edits'))

    return ImprovePromptResponse(
        run_id=run_id,
        transcript=transcript,
        metrics=metrics,
        improved_prompt=improved_prompt
    )