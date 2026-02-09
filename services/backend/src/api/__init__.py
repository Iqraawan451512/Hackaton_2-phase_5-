# [Task]: T023, T028-T032, T048, T065-T067 — FastAPI app with all routes
"""Backend Service FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.jobs import router as jobs_router
from src.api.tasks import router as tasks_router
from src.api.websocket import router as ws_router
from src.config import DAPR_PUBSUB_NAME, STANDALONE_MODE, configure_logging
from src.events.task_updates_handler import handle_task_update

configure_logging("backend")

app = FastAPI(
    title="Todo Chatbot Backend",
    version="1.0.0",
    description="Backend Service for Phase V Todo Chatbot",
)

# CORS — required for Hugging Face Spaces cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(jobs_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "service": "backend"}


if not STANDALONE_MODE:
    # Dapr subscription for task-updates topic (self-subscribe for WebSocket relay)
    @app.get("/dapr/subscribe")
    async def subscribe() -> list[dict]:
        """Return Dapr Pub/Sub subscriptions for this service."""
        return [
            {
                "pubsubname": DAPR_PUBSUB_NAME,
                "topic": "task-updates",
                "route": "/events/task-updates",
            }
        ]


@app.post("/events/task-updates")
async def receive_task_update(request: Request) -> dict:
    """Receive task-update events for WebSocket relay."""
    body = await request.json()
    event_data = body.get("data", body)
    await handle_task_update(event_data)
    return {"status": "SUCCESS"}
