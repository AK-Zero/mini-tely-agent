
from twilio.rest import Client
from livekit import api
import json
import logging

from ..model.call_request import CallRequest

logger = logging.getLogger("main-service")
logger.setLevel(logging.INFO)

class MainService:
    def __init__(self):
        logger.info("MainService initialized.")

    async def validate_phone_number(self, phone_number: str, twilio_client: Client) -> bool:
        try:
            incoming_numbers = twilio_client.incoming_phone_numbers.list(
                phone_number=phone_number
            )
            if incoming_numbers:
                return True
            
            outgoing_caller_ids = twilio_client.outgoing_caller_ids.list(
                phone_number=phone_number
            )
            if outgoing_caller_ids:
                return True
            
            return False
        except Exception as e:
            print(f"Error validating phone number: {e}")
            return False
        
    async def create_livekit_room_and_dispatch_agent(
        self, 
        room_name: str, 
        request: CallRequest,
        agent_instructions: str,
        livekit_api: api.LiveKitAPI,
    ) -> dict:
        """
        Create a LiveKit room and dispatch an AI agent to handle the call.
        """
        try:
            # Create room
            room_request = api.CreateRoomRequest(
                name=room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=2
            )
            room = await livekit_api.room.create_room(room_request)
            
            # Dispatch agent with custom metadata including instructions
            dispatch_request = api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="debt-collection-agent",  # This should match your agent name
                metadata=json.dumps({
                    "instructions": agent_instructions,
                    "phone_number": request.phone_number,
                    "customer_name": request.customer_name,  
                    "card_number_ending": request.card_number_ending,
                    "amount_due": request.amount_due,
                    "call_type": "outbound"
                })
            )
            
            dispatch = await livekit_api.agent_dispatch.create_dispatch(dispatch_request)
            
            return {
                "room": room,
                "dispatch": dispatch.id,
                "success": True
            }
        except Exception as e:
            print(f"Error creating LiveKit room and dispatching agent: {e}")
            return {
                "error": str(e),
                "success": False
            }

    async def place_outbound_call_with_livekit(
        self, 
        phone_number: str, 
        room_name: str,
        livekit_api: api.LiveKitAPI,
        sip_trunk_id: str
    ) -> dict:
        """
        Place outbound call and connect it to LiveKit room via SIP.
        """
        try:
            # Create SIP participant for outbound call
            sip_request = api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                participant_identity=phone_number,
                wait_until_answered=True
            )
            
            sip_participant = await livekit_api.sip.create_sip_participant(sip_request)
            
            return {
                "sip_participant": sip_participant,
                "success": True
            }
        except api.TwirpError as e:
            error_msg = f"SIP Error: {e.message}"
            if e.metadata:
                error_msg += f", Status: {e.metadata.get('sip_status_code')} {e.metadata.get('sip_status')}"
            
            return {
                "error": error_msg,
                "success": False
            }