# [Task]: T040 — Recurring Task Service FastAPI application
"""Recurring Task Service FastAPI application."""

from fastapi import FastAPI, Request

from src.config import DAPR_PUBSUB_NAME, configure_logging
from src.handlers.task_events import handle_task_event

configure_logging("recurring-task")

app = FastAPI(
    title="Todo Chatbot Recurring Task Service",
    version="1.0.0",
    description="Recurring Task Service — creates next task instances on completion",
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "service": "recurring-task"}


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
