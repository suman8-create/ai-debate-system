import uuid
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from db.supabase_client import supabase_store
from api.websocket import start_debate_async_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debates", tags=["Debates"])

class CreateDebateRequest(BaseModel):
    topic: str = Field(..., example="Should college education be tuition-free?")
    max_rounds: int = Field(default=2, ge=1, le=8, example=2)

class CreateDebateResponse(BaseModel):
    session_id: str
    topic: str
    max_rounds: int
    status: str
    websocket_url: str

@router.post("", response_model=CreateDebateResponse)
async def create_debate_session(payload: CreateDebateRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    
    # 1. Initialize Supabase Session
    try:
        if hasattr(supabase_store, "create_debate_session"):
            supabase_store.create_debate_session(
                session_id=session_id,
                topic=payload.topic,
                rounds=payload.max_rounds
            )
    except Exception as e:
        logger.warning(f"Could not persist session to Supabase: {e}")

    # 2. Schedule non-blocking thread execution
    background_tasks.add_task(start_debate_async_task, session_id, payload.topic, payload.max_rounds)

    return CreateDebateResponse(
        session_id=session_id,
        topic=payload.topic,
        max_rounds=payload.max_rounds,
        status="RUNNING",
        websocket_url=f"/ws/debates/{session_id}"
    )