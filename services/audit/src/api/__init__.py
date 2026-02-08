# [Task]: T033 — Audit Service FastAPI application with Dapr subscription
"""Audit Service FastAPI application."""

from fastapi import FastAPI, Request

from src.config import DAPR_PUBSUB_NAME, configure_logging
from src.handlers.task_events import handle_task_event

configure_logging("audit")

app = FastAPI(
    title="Todo Chatbot Audit Service",
    version="1.0.0",
    description="Audit Service — consumes task events and persists audit logs",
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "service": "audit"}


# Dapr subscription configuration
@app.get("/dapr/subscribe")
async def subscribe() -> list[dict]:
    """Return Dapr Pub/Sub subscriptions for this service."""
    return [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "task-events",
            "route": "/events/task-events",
        }
    ]


@app.post("/events/task-events")
async def receive_task_event(request: Request) -> dict:
    """Receive task events from Dapr Pub/Sub."""
    body = await request.json()
    event_data = body.get("data", body)
    await handle_task_event(event_data)
    return {"status": "SUCCESS"}
