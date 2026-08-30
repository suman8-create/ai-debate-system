import json
import logging
import asyncio
from typing import Dict, Any, List
from fastapi import WebSocket
from graph.controller import debate_graph

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active real-time WebSocket connections and message replay buffers."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.event_buffers: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

        # Replay any events that fired before connection established
        if session_id in self.event_buffers:
            for payload in self.event_buffers[session_id]:
                try:
                    await websocket.send_text(json.dumps(payload, default=str))
                except Exception as e:
                    logger.warning(f"Replay send failed for {session_id}: {e}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def broadcast_event(self, session_id: str, event_type: str, data: Any):
        payload = {
            "event": event_type,
            "session_id": session_id,
            "data": data
        }
        
        # Buffer event
        if session_id not in self.event_buffers:
            self.event_buffers[session_id] = []
        self.event_buffers[session_id].append(payload)

        # Broadcast if connection exists
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            try:
                await ws.send_text(json.dumps(payload, default=str))
            except Exception as e:
                logger.warning(f"Failed to stream WS payload to {session_id}: {e}")

manager = ConnectionManager()

def run_graph_sync(session_id: str, topic: str, max_rounds: int, loop: asyncio.AbstractEventLoop):
    """Executes the synchronous LangGraph debate engine safely inside a worker thread."""
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

    # Dispatch start event
    asyncio.run_coroutine_threadsafe(
        manager.broadcast_event(session_id, "DEBATE_STARTED", {"topic": topic, "max_rounds": max_rounds}),
        loop
    )

    try:
        for chunk in debate_graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_update in chunk.items():
                logger.info(f"LangGraph Stream Node: {node_name}")

                if node_name == "research":
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast_event(session_id, "STAGE_RESEARCH_COMPLETE", {
                            "message": "Evidence indexed"
                        }),
                        loop
                    )

                elif node_name == "pro_generate":
                    pro_arg = node_update.get("current_pro_arg")
                    if pro_arg:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_event(session_id, "PRO_ARGUMENT_DELIVERED", pro_arg.model_dump()),
                            loop
                        )

                elif node_name == "pro_audit":
                    audit = node_update.get("pro_audit_result")
                    if audit:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_event(session_id, "PRO_AUDIT_VERDICT", audit.model_dump()),
                            loop
                        )

                elif node_name == "con_generate":
                    con_arg = node_update.get("current_con_arg")
                    if con_arg:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_event(session_id, "CON_ARGUMENT_DELIVERED", con_arg.model_dump()),
                            loop
                        )

                elif node_name == "con_audit":
                    audit = node_update.get("con_audit_result")
                    if audit:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_event(session_id, "CON_AUDIT_VERDICT", audit.model_dump()),
                            loop
                        )

                elif node_name == "conflict_resolver":
                    conflicts = node_update.get("conflict_history", [])
                    if conflicts:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_event(session_id, "CONFLICT_RESOLVED", conflicts[-1].model_dump()),
                            loop
                        )

                elif node_name == "judge":
                    verdict = node_update.get("judge_verdict")
                    winner = node_update.get("winner")
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast_event(session_id, "DEBATE_COMPLETED", {
                            "winner": winner,
                            "judge_verdict": verdict.model_dump() if hasattr(verdict, "model_dump") else verdict
                        }),
                        loop
                    )

    except Exception as e:
        logger.error(f"Error in threaded debate: {e}")
        asyncio.run_coroutine_threadsafe(
            manager.broadcast_event(session_id, "DEBATE_ERROR", {"error": str(e)}),
            loop
        )

async def start_debate_async_task(session_id: str, topic: str, max_rounds: int = 2):
    """Spawns debate execution in a separate OS thread to keep the asyncio event loop free."""
    loop = asyncio.get_running_loop()
    await asyncio.to_thread(run_graph_sync, session_id, topic, max_rounds, loop)