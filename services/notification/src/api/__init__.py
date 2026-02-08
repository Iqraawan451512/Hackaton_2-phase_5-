# [Task]: T051 — Notification Service FastAPI application
"""Notification Service FastAPI application."""

from fastapi import FastAPI, Request

from src.config import DAPR_PUBSUB_NAME, configure_logging
from src.handlers.reminders import handle_reminder

configure_logging("notification")

app = FastAPI(
    title="Todo Chatbot Notification Service",
    version="1.0.0",
    description="Notification Service — delivers reminder notifications",
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "service": "notification"}


@app.get("/dapr/subscribe")
async def subscribe() -> list[dict]:
    """Return Dapr Pub/Sub subscriptions for this service."""
    return [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "reminders",
            "route": "/events/reminders",
        }
    ]


@app.post("/events/reminders")
async def receive_reminder(request: Request) -> dict:
    """Receive reminder events from Dapr Pub/Sub."""
    body = await request.json()
    event_data = body.get("data", body)
    await handle_reminder(event_data)
    return {"status": "SUCCESS"}
