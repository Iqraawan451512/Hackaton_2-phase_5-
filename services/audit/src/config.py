# [Task]: T033 — Audit Service configuration
"""Configuration for the Audit Service."""

import json
import logging
import sys
from typing import Any, Optional

import structlog
from dapr.clients import DaprClient

DAPR_STORE_NAME = "statestore"
DAPR_PUBSUB_NAME = "kafka-pubsub"


def configure_logging(service_name: str = "audit") -> None:
    """Configure structured JSON logging for the service."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(
            file=sys.stdout
        ),
    )
    logger = structlog.get_logger()
    logger.info("logging_configured", service=service_name)


def get_logger(name: str = "audit") -> structlog.BoundLogger:
    """Get a named structured logger."""
    return structlog.get_logger(service=name)


class StateStore:
    """Dapr state store wrapper for the Audit Service."""

    def __init__(self, store_name: str = DAPR_STORE_NAME):
        self.store_name = store_name

    def save(self, key: str, value: Any) -> None:
        """Save a value to the Dapr state store."""
        with DaprClient() as client:
            client.save_state(
                store_name=self.store_name,
                key=key,
                value=json.dumps(value),
            )

    def get(self, key: str) -> Optional[dict]:
        """Get a value from the Dapr state store."""
        with DaprClient() as client:
            state = client.get_state(
                store_name=self.store_name, key=key
            )
            if state.data:
                return json.loads(state.data)
            return None
