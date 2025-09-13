import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    SIP_TRUNK_ID = os.getenv("SIP_TRUNK_ID")

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

    MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
    MODEL_NAME = os.getenv("MODEL_NAME")
    MODEL_KEY = os.getenv("MODEL_KEY")
    MODEL_GENERATE_URL = os.getenv("MODEL_GENERATE_URL")
    SOURCE_DIRECTORY = os.getenv("SOURCE_DIRECTORY")
    DESTINATION_DIRECTORY = os.getenv("DESTINATION_DIRECTORY")
    PROCESSED_DIRECTORY = os.getenv("PROCESSED_DIRECTORY")

