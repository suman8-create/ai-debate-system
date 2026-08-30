import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from graph.controller import debate_graph
from graph.state import DebateState

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active real-time WebSocket connections per debate session."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def broadcast_event(self, session_id: str, event_type: str, data: Any):
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            try:
                payload = {
                    "event": event_type,
                    "session_id": session_id,
                    "data": data
                }
                await ws.send_text(json.dumps(payload, default=str))
            except Exception as e:
                logger.warning(f"Failed to stream WS payload to {session_id}: {e}")

manager = ConnectionManager()

async def stream_debate_execution(session_id: str, topic: str, max_rounds: int = 2):
    """Executes the LangGraph debate engine while streaming granular node events over WebSocket."""
    initial_state = {
        "session_id": session_id,
        "topic": topic,
        "current_round": 1,
        "max_rounds": max_rounds,
        "max_revisions": 2,
        "pro_revision_count": 0,
        "con_revision_count": 0,
        "current_pro_arg": None,
        "current_con_arg": None,
        "pro_audit_result": None,
        "con_audit_result": None,
        "arguments": [],
        "audit_history": [],
        "conflict_history": [],
        "winner": None,
        "judge_verdict": None
    }

    await manager.broadcast_event(session_id, "DEBATE_STARTED", {"topic": topic, "max_rounds": max_rounds})

    try:
        # Stream LangGraph state events node by node
        for chunk in debate_graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_update in chunk.items():
                logger.info(f"LangGraph Stream Node Executed: {node_name}")

                if node_name == "research":
                    await manager.broadcast_event(session_id, "STAGE_RESEARCH_COMPLETE", {
                        "message": "Web search and atomic evidence indexing finished."
                    })

                elif node_name == "pro_generate":
                    pro_arg = node_update.get("current_pro_arg")
                    if pro_arg:
                        await manager.broadcast_event(session_id, "PRO_ARGUMENT_DELIVERED", pro_arg.model_dump())

                elif node_name == "pro_audit":
                    audit = node_update.get("pro_audit_result")
                    if audit:
                        await manager.broadcast_event(session_id, "PRO_AUDIT_VERDICT", audit.model_dump())

                elif node_name == "con_generate":
                    con_arg = node_update.get("current_con_arg")
                    if con_arg:
                        await manager.broadcast_event(session_id, "CON_ARGUMENT_DELIVERED", con_arg.model_dump())

                elif node_name == "con_audit":
                    audit = node_update.get("con_audit_result")
                    if audit:
                        await manager.broadcast_event(session_id, "CON_AUDIT_VERDICT", audit.model_dump())

                elif node_name == "conflict_resolver":
                    conflicts = node_update.get("conflict_history", [])
                    if conflicts:
                        latest_conflict = conflicts[-1]
                        await manager.broadcast_event(session_id, "CONFLICT_RESOLVED", latest_conflict.model_dump())

                elif node_name == "judge":
                    verdict = node_update.get("judge_verdict")
                    winner = node_update.get("winner")
                    await manager.broadcast_event(session_id, "DEBATE_COMPLETED", {
                        "winner": winner,
                        "judge_verdict": verdict
                    })

    except Exception as e:
        logger.error(f"Error during streamed debate execution: {e}")
        await manager.broadcast_event(session_id, "DEBATE_ERROR", {"error": str(e)})