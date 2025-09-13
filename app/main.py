from fastapi import FastAPI
from twilio.rest import Client
from livekit import api
from contextlib import asynccontextmanager
import logging
from .config.config import Config
from .service.agent import DebtCollectionAgentWorker
from .router.agent_router import router as agent_router
from .router.testing_router import router as testing_router

logging.basicConfig(level=logging.INFO)

config = Config()

agent_worker = DebtCollectionAgentWorker(config=config)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await agent_worker.start_worker()
    logging.info("FastAPI app started.")
    yield
    await agent_worker.stop_worker()
    logging.info("FastAPI app is shutting down.")

app = FastAPI(
    lifespan=lifespan,
    title="Debt Collection Voice Agent API",
    description="API for initiating automated debt collection calls using LiveKit and Twilio.",
    version="1.0.0",
    docs_url="/docs",   
    redoc_url="/redoc" 
)

app.include_router(agent_router)
app.include_router(testing_router)

@app.get("/")
def read_root():
    return {"message": "Debt Collection Voice Agent API is running. Go to /docs for the API explorer."}