# [Task]: T020, T027 — Dapr Pub/Sub publishing wrapper with task event helper
"""Event publisher for Dapr Pub/Sub topics."""

import json
from typing import Any

from dapr.clients import DaprClient

from src.config import DAPR_PUBSUB_NAME, get_logger
from src.events.task_event import TaskEvent

logger = get_logger("event_publisher")

# Approved Kafka topics (Constitution Principle X)
TOPIC_TASK_EVENTS = "task-events"
TOPIC_REMINDERS = "reminders"
TOPIC_TASK_UPDATES = "task-updates"


class EventPublisher:
    """Publishes events to Kafka topics via Dapr Pub/Sub."""

    def __init__(self, pubsub_name: str = DAPR_PUBSUB_NAME):
        self.pubsub_name = pubsub_name

    def publish(
        self, topic: str, data: dict[str, Any]
    ) -> None:
        """Publish an event to a Dapr Pub/Sub topic."""
        with DaprClient() as client:
            client.publish_event(
                pubsub_name=self.pubsub_name,
                topic_name=topic,
                data=json.dumps(data),
                data_content_type="application/json",
            )
        logger.info(
            "event_published",
            topic=topic,
            event_type=data.get("event_type", "unknown"),
        )

    def publish_task_event(self, event: TaskEvent) -> None:
        """Publish a TaskEvent to the task-events topic.

        Convenience method that serializes the TaskEvent model
        and publishes to the task-events topic.
        """
        self.publish(
            TOPIC_TASK_EVENTS, event.model_dump(mode="json")
        )

    def publish_task_update(
        self,
        event_type: str,
        task_id: str,
        task_data: dict[str, Any],
    ) -> None:
        """Publish a task-update event for real-time client sync.

        Sends the current task state to the task-updates topic
        so WebSocket clients receive live updates.
        """
        self.publish(TOPIC_TASK_UPDATES, {
            "event_type": event_type,
            "task_id": task_id,
            "task": task_data,
        })
