import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from db.supabase_client import supabase_store
from api.websocket import stream_debate_execution

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debates", tags=["Debates"])

class CreateDebateRequest(BaseModel):
    topic: str = Field(..., example="Should college education be free?")
    max_rounds: int = Field(default=2, ge=1, le=4, example=2)

class CreateDebateResponse(BaseModel):
    session_id: str
    topic: str
    max_rounds: int
    status: str
    websocket_url: str

@router.post("", response_model=CreateDebateResponse)
async def create_debate_session(payload: CreateDebateRequest, background_tasks: BackgroundTasks):
    """Creates a new debate session and schedules the execution graph in the background."""
    session_id = str(uuid.uuid4())
    
    # 1. Initialize record in Supabase
    try:
        supabase_store.create_debate_session(
            session_id=session_id,
            topic=payload.topic,
            rounds=payload.max_rounds
        )
    except Exception as e:
        logger.warning(f"Could not persist session to Supabase: {e}")

    # 2. Schedule live streaming workflow
    background_tasks.add_task(stream_debate_execution, session_id, payload.topic, payload.max_rounds)

    return CreateDebateResponse(
        session_id=session_id,
        topic=payload.topic,
        max_rounds=payload.max_rounds,
        status="RUNNING",
        websocket_url=f"/ws/debates/{session_id}"
    )

@router.get("/{session_id}")
async def get_debate_session(session_id: str):
    """Fetches the debate session record, status, and metadata."""
    try:
        response = supabase_store.client.table("debate_sessions").select("*").eq("id", session_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Debate session not found.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/arguments")
async def get_debate_arguments(session_id: str):
    """Retrieves all structured arguments for a given session."""
    try:
        response = supabase_store.client.table("arguments").select("*").eq("session_id", session_id).order("created_at").execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/adjudication")
async def get_adjudication_verdict(session_id: str):
    """Retrieves the final judge scorecards and adjudication rationale."""
    try:
        response = supabase_store.client.table("debate_sessions").select("winner, metadata").eq("id", session_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Debate session not found.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))