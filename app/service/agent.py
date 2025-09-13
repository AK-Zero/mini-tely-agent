import json
import asyncio
import logging
import os
import aiofiles

from httpx import Timeout
from datetime import datetime

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    function_tool,
    Worker
)
from livekit.plugins import openai, silero, deepgram, elevenlabs
from livekit import api
# from livekit.plugins.turn_detector.multilingual import MultilingualModel

from ..config.config import Config
from ..constant.prompt_constants import DEFAULT_AGENT_INSTRUCTIONS, DEFAULT_INITIAL_GREETING

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)


class DebtCollectionAgent:
    def __init__(self):
        self.instructions = None
        self.job_context = None
        self.session = None
        self.config = Config()
        os.makedirs(os.path.join(os.sep, self.config.SOURCE_DIRECTORY), exist_ok=True)
        os.makedirs(os.path.join(os.sep, self.config.DESTINATION_DIRECTORY), exist_ok=True)
        os.makedirs(os.path.join(os.sep, self.config.PROCESSED_DIRECTORY), exist_ok=True)

    async def start(self, ctx: JobContext):
        await ctx.connect()
        self.job_context = ctx

        metadata = json.loads(ctx.job.metadata or "{}")
        instructions = metadata.get("instructions")

        if instructions is None:
            instructions = DEFAULT_AGENT_INSTRUCTIONS

        agent = Agent(
            instructions=instructions,
            # tools=[self.end_call_tool]
        )

        session = AgentSession(
            stt=deepgram.STT(
                api_key=self.config.DEEPGRAM_API_KEY,
                model="nova-3",
                language="multi"
            ),
            llm=openai.LLM(
                model=self.config.MODEL_NAME,
                base_url=self.config.MODEL_BASE_URL,
                api_key=self.config.MODEL_KEY,
                timeout=Timeout(60),
                temperature=0.4,  
            ),
            tts=elevenlabs.TTS(
                api_key=self.config.ELEVENLABS_API_KEY,
                model="eleven_turbo_v2"
            ),
            vad=silero.VAD.load(),
            # turn_detector=MultilingualModel(),
            min_endpointing_delay=0.5,
            max_endpointing_delay=4.0,
            allow_interruptions=True,
        )
    
        await session.start(agent=agent, room=ctx.room)
        self.session = session

        # For outbound calls, generate initial greeting
        try:
            phone_number = metadata.get("phone_number")
            if metadata.get("call_type") == "outbound":
                await ctx.wait_for_participant(identity=phone_number)
                await session.say(
                    text=DEFAULT_INITIAL_GREETING.replace("{customer_name}", metadata.get("customer_name", "Customer")),
                    allow_interruptions=True
                )
        except Exception as e:
            logger.info(f"Error generating initial greeting: {e}")

        async def write_transcript():
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.config.SOURCE_DIRECTORY, f"transcript_{ctx.room.name}_{current_date}.json")

            cust_info = {
                "customer_name": metadata.get("customer_name", "N/A"),
                "phone_number": metadata.get("phone_number", "N/A"),
                "card_number_ending": metadata.get("card_number_ending", "N/A"),
                "amount_due": metadata.get("amount_due", "N/A")
            }

            session_history_list = session.history.to_dict()
            session_history_dict = session_history_list.get("items", [])
            desired_keys = ["role", "content"]
            filtered_transcript = [
                {key: message[key] for key in desired_keys if key in message}
                for message in session_history_dict
            ]
            output_data = {
                "customer_info": cust_info,
                "transcript": filtered_transcript
            }
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps(output_data, indent=2))
            print(f"Transcript for {ctx.room.name} saved to {filename}")

        ctx.add_shutdown_callback(write_transcript)

    @function_tool(description="End the call by saying goodbye and terminating the connection. Usage: end_call_tool(reason='call completed')")
    async def end_call_tool(self, reason: str = "call completed"):
        """
        Ends the LiveKit call with a proper goodbye message.
        Args:
            reason (str): Brief reason for ending the call. Default is 'call completed'.
        """
        try:
            if not self.job_context or not self.job_context.room:
                logger.error("No active call session found")
                return "Error: No active call session"

            room_name = self.job_context.room.name
            logger.info(f"Ending call for room: {room_name} - Reason: {reason}")

            goodbye_messages = [
                "I appreciate your time today.",
                "Thank you for speaking with me.",
                "Have a great rest of your day!"
            ]
            
            for message in goodbye_messages:
                await self.session.say(text=message, allow_interruptions=False)
                await asyncio.sleep(0.5)  

            await asyncio.sleep(2)
            livekit_api = api.LiveKitAPI(
                url=self.config.LIVEKIT_URL,
                api_key=self.config.LIVEKIT_API_KEY,
                api_secret=self.config.LIVEKIT_API_SECRET
            )
            delete_request = api.DeleteRoomRequest(room=room_name)
            await livekit_api.room.delete_room(delete_request)
            return "Call ended successfully"

        except Exception as e:
            logger.error(f"Error ending call: {e}", exc_info=True)
            return f"Failed to end call: {str(e)}"


async def entrypoint(ctx: JobContext):
    agent = DebtCollectionAgent()
    await agent.start(ctx)


class DebtCollectionAgentWorker:
    def __init__(self, config: Config):
        self.worker = None
        self.worker_task = None
        self.config = config

    async def start_worker(self):
        try:
            logger.info("🚀 Starting LiveKit Agent Worker...")
            worker_options = WorkerOptions(
                entrypoint_fnc=entrypoint,
                ws_url=self.config.LIVEKIT_URL,
                api_key=self.config.LIVEKIT_API_KEY,
                api_secret=self.config.LIVEKIT_API_SECRET,
                agent_name="debt-collection-agent",
            )
            self.worker = Worker(worker_options)
            self.worker_task = asyncio.create_task(self.worker.run())
            logger.info("✅ LiveKit Agent Worker started successfully")
            return True
        except Exception as e:
            logger.info(f"❌ Failed to start agent worker: {e}")
            return False

    async def stop_worker(self):
        if self.worker:
            await self.worker.aclose()
        if self.worker_task:
            self.worker_task.cancel()