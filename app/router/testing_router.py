import uuid
import logging
from fastapi import APIRouter

from ..service.testing_service import TestingService
from ..model.improve_prompt_request import ImprovePromptRequest
from ..model.improve_prompt_response import ImprovePromptResponse
from ..model.improve_prompt_request_auto import ImprovePromptRequestAuto

router = APIRouter(
    prefix="/testing",
    tags=["testing"],
)

logger = logging.getLogger("testing-router")
logging.basicConfig(level=logging.INFO)

testing_service = TestingService()

@router.post("/train/prompt", response_model=ImprovePromptResponse, summary="Train and improve the agent prompt based on simulated conversations and evaluations.")
async def train_prompt(req: ImprovePromptRequest):
    run_id = str(uuid.uuid4())
    
    improved_prompts = []
    transcripts = []
    all_metrics = []
    
    for persona in req.personas:
        logger.info(f"Starting simulation for persona: {persona.name}")
        transcript = await testing_service.run_simulation(
            req.base_agent_prompt, 
            persona.persona_prompt, 
            req.max_turns
        )
        transcripts.append(transcript)

        metrics = await testing_service.evaluate_conversation(transcript)
        all_metrics.append(metrics)
        
        improved_prompt = await testing_service.rewrite_prompt_text(
            req.base_agent_prompt, 
            metrics.get('recommended_prompt_edits')
        )
        improved_prompts.append(improved_prompt)
    
    final_improved_prompt = await testing_service.combine_prompt_revisions(req.base_agent_prompt,improved_prompts)
    
    return ImprovePromptResponse(
        run_id=run_id,
        transcripts=transcripts,
        metrics=all_metrics,
        improved_prompts=improved_prompts,
        final_improved_prompt=final_improved_prompt
    )

@router.post("/train/prompt/auto", response_model=ImprovePromptResponse, description="Automatically generates personas and runs simulations to improve the agent prompt.")
async def train_prompt_auto(req: ImprovePromptRequestAuto):
    run_id = str(uuid.uuid4())

    personas = await testing_service.generate_personas(req.persona_names)
    
    improved_prompts = []
    transcripts = []
    all_metrics = []
    
    for persona in personas:
        transcript = await testing_service.run_simulation(
            req.base_agent_prompt, 
            persona, 
            req.max_turns
        )
        transcripts.append(transcript)

        metrics = await testing_service.evaluate_conversation(transcript)
        all_metrics.append(metrics)
        
        improved_prompt = await testing_service.rewrite_prompt_text(
            req.base_agent_prompt, 
            metrics.get('recommended_prompt_edits')
        )
        improved_prompts.append(improved_prompt)
    
    final_improved_prompt = await testing_service.combine_prompt_revisions(req.base_agent_prompt,improved_prompts)
    
    return ImprovePromptResponse(
        run_id=run_id,
        transcripts=transcripts,
        metrics=all_metrics,
        improved_prompts=improved_prompts,
        final_improved_prompt=final_improved_prompt
    )