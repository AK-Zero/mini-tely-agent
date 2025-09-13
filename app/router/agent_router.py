import uuid
import logging
from fastapi import APIRouter, HTTPException
from livekit import api
from twilio.rest import Client
from ..config.config import Config
from ..service.main_service import MainService
from ..service.summarize_transcript_service import InsightsService
from ..model.call_request import CallRequest
from ..model.call_response import CallResponse
from ..constant.prompt_constants import DEFAULT_AGENT_INSTRUCTIONS

router = APIRouter(
    prefix="/api",
    tags=["agent"],
)

config = Config()
main_service = MainService()
insights_service = InsightsService()
twilio_client = Client(
    username=config.TWILIO_ACCOUNT_SID, 
    password=config.TWILIO_AUTH_TOKEN)

livekit_api = api.LiveKitAPI(config.LIVEKIT_URL, config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)

@router.post("/initiate/call", response_model=CallResponse)
async def initiate_call(request: CallRequest):
    """
    This endpoint initiates a debt collection call.
    It creates a LiveKit room, and then uses Twilio to dial out and connect the call to the room.
    """
    try:
        call_id = str(uuid.uuid4())
        room_name = f"debt-collection-{request.phone_number.replace('+', '')}"
        logging.info(f"Initiating call to {request.phone_number} in room {room_name}")

        enhanced_instructions = DEFAULT_AGENT_INSTRUCTIONS. \
        replace("{customer_name}", request.customer_name). \
        replace("{amount_due}", f"{request.amount_due}"). \
        replace("{card_number_ending}", request.card_number_ending) 

        livekit_result = await main_service.create_livekit_room_and_dispatch_agent(
            room_name=room_name, 
            request=request,
            agent_instructions=request.agent_instructions or enhanced_instructions,
            livekit_api=livekit_api
        )
        
        if not livekit_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to setup LiveKit: {livekit_result['error']}"
            )
        
        call_result = await main_service.place_outbound_call_with_livekit(
            phone_number=request.phone_number, 
            room_name=room_name,
            livekit_api=livekit_api,
            sip_trunk_id=config.SIP_TRUNK_ID
        )
        
        if not call_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to place call: {call_result['error']}"
            )
        
        return CallResponse(
            call_id=call_id,
            room_name=room_name,
            status="success",
            message=f"Call initiated to {request.phone_number}"
        )

    except Exception as e:
        logging.error(f"Error initiating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/call-status/{room_name}")
async def get_call_status(room_name: str):
    """
    Get the status of an ongoing call.
    """
    try:
        room_request = api.ListRoomsRequest(names=[room_name])
        rooms = await livekit_api.room.list_rooms(room_request)
        
        if not rooms.rooms:
            return {"status": "not_found", "message": "Room not found"}
        
        room = rooms.rooms[0]
        
        participants_request = api.ListParticipantsRequest(room=room_name)
        participants = await livekit_api.room.list_participants(participants_request)
        
        return {
            "status": "active" if room.num_participants > 0 else "empty",
            "room_name": room_name,
            "num_participants": room.num_participants,
            "participants": [p.identity for p in participants.participants],
            "creation_time": room.creation_time
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/hangup/{room_name}")
async def hangup_call(room_name: str):
    """
    End a call by deleting the room.
    """
    try:
        delete_request = api.DeleteRoomRequest(room=room_name)
        await livekit_api.room.delete_room(delete_request)
        
        return {"status": "success", "message": f"Call in room {room_name} ended"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/debug/test-dispatch/{room_name}")
async def test_dispatch(room_name: str):
    try:
        room_request = api.CreateRoomRequest(name=room_name)
        room = await livekit_api.room.create_room(room_request)
        
        dispatch_request = api.CreateAgentDispatchRequest(
            room=room_name,
            agent_name="debt-collection-agent"
        )
        dispatch = await livekit_api.agent_dispatch.create_dispatch(dispatch_request)
        
        return {"success": True, "room": room.name, "dispatch": dispatch.id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/generate/insights")
async def generate_insights():
    """
    Generate insights from all transcript files in the source directory.
    """
    try:
        batch_insights = insights_service.generate()
        return {"status": "success", "Batch Insights" : batch_insights}
        
    except Exception as e:
        logging.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))