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

@router.get("/history")
async def get_debate_history():
    """Fetches past debate sessions from Supabase."""
    if not supabase_store.client:
        return []
    try:
        res = (
            supabase_store.client.table("debate_sessions")
            .select("id, topic, status, created_at, metadata")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.warning(f"Error fetching history: {e}")
        return []

@router.get("/{session_id}")
async def get_debate_session_details(session_id: str):
    """Fetches complete debate transcript and adjudication for a historical session."""
    if not supabase_store.client:
        raise HTTPException(status_code=503, detail="Database client unavailable")

    try:
        session_res = supabase_store.client.table("debate_sessions").select("*").eq("id", session_id).single().execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        args_res = supabase_store.client.table("arguments").select("*").eq("session_id", session_id).execute()
        args_data = args_res.data or []
        args_data.sort(key=lambda x: x.get("round_number", 0))

        conflicts_data = []
        try:
            conflicts_res = supabase_store.client.table("conflict_resolutions").select("*").eq("session_id", session_id).execute()
            conflicts_data = conflicts_res.data or []
            conflicts_data.sort(key=lambda x: x.get("round_number", x.get("round", 0)))
        except Exception as ce:
            logger.warning(f"Could not load conflicts for {session_id}: {ce}")

        return {
            "session": session_res.data,
            "arguments": args_data,
            "conflicts": conflicts_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session details: {e}")
        raise HTTPException(status_code=500, detail=str(e))