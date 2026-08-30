import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as debates_router
from api.websocket import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Multi-Agent Debate Engine ",
    description="Autonomous dialectical debate system with empirical RAG, live auditing, and LangGraph orchestration.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routes
app.include_router(debates_router)

# Register WebSocket Endpoint
@app.websocket("/ws/debates/{session_id}")
async def debate_websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    try:
        while True:
            # Keep socket alive and accept potential client heartbeats
            data = await websocket.receive_text()
            logger.info(f"WS received from client ({session_id}): {data}")
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.warning(f"WS error ({session_id}): {e}")
        manager.disconnect(session_id)

@app.get("/")
def health_check():
    return {
        "status": "ONLINE",
        "service": "AI Debate Engine",
        "endpoints": {
            "docs": "/docs",
            "create_debate": "POST /api/debates",
            "live_stream": "WS /ws/debates/{session_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)