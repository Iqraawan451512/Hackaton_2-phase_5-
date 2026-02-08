# [Task]: T037 — Unit tests for EventPublisher
"""Tests for EventPublisher with mocked Dapr client."""

from unittest.mock import MagicMock, patch

from src.events.publisher import EventPublisher, TOPIC_TASK_EVENTS
from src.events.task_event import TaskEvent, TaskEventType


class TestEventPublisher:
    """Tests for the EventPublisher class."""

    @patch("src.events.publisher.DaprClient")
    def test_publish_calls_dapr(self, mock_dapr_cls):
        mock_client = MagicMock()
        mock_dapr_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_dapr_cls.return_value.__exit__ = MagicMock(
            return_value=False
        )

        publisher = EventPublisher(pubsub_name="test-pubsub")
        publisher.publish("test-topic", {"key": "value"})

        mock_client.publish_event.assert_called_once()
        call_kwargs = mock_client.publish_event.call_args[1]
        assert call_kwargs["pubsub_name"] == "test-pubsub"
        assert call_kwargs["topic_name"] == "test-topic"
        assert call_kwargs["data_content_type"] == "application/json"

    @patch("src.events.publisher.DaprClient")
    def test_publish_task_event(self, mock_dapr_cls):
        mock_client = MagicMock()
        mock_dapr_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_dapr_cls.return_value.__exit__ = MagicMock(
            return_value=False
        )

        publisher = EventPublisher(pubsub_name="test-pubsub")
        event = TaskEvent(
            event_type=TaskEventType.CREATED,
            task_id="task-1",
            payload={"task": {"title": "Test"}},
            user_id="user-1",
        )
        publisher.publish_task_event(event)

        mock_client.publish_event.assert_called_once()
        call_kwargs = mock_client.publish_event.call_args[1]
        assert call_kwargs["topic_name"] == TOPIC_TASK_EVENTS

    @patch("src.events.publisher.DaprClient")
    def test_publish_uses_correct_pubsub_name(self, mock_dapr_cls):
        mock_client = MagicMock()
        mock_dapr_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_dapr_cls.return_value.__exit__ = MagicMock(
            return_value=False
        )

        publisher = EventPublisher(pubsub_name="custom-pubsub")
        publisher.publish("topic", {"data": 1})

        call_kwargs = mock_client.publish_event.call_args[1]
        assert call_kwargs["pubsub_name"] == "custom-pubsub"

    def test_default_pubsub_name(self):
        publisher = EventPublisher()
        assert publisher.pubsub_name == "kafka-pubsub"
