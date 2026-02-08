# [Task]: T019, T021, T022 — Dapr client wrappers and logging config
"""Configuration for the Backend Service.

Provides Dapr client wrappers for state store, secrets, and
structured logging configuration.
"""

import json
import logging
import sys
from typing import Any, Optional

import structlog
from dapr.clients import DaprClient

# ── Constants ──────────────────────────────────────────────────
DAPR_STORE_NAME = "statestore"
DAPR_PUBSUB_NAME = "kafka-pubsub"
DAPR_SECRET_STORE = "kubernetes-secrets"


# ── T022: Structured logging ──────────────────────────────────

def configure_logging(service_name: str = "backend") -> None:
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


def get_logger(name: str = "backend") -> structlog.BoundLogger:
    """Get a named structured logger."""
    return structlog.get_logger(service=name)


# ── T019: State store operations ──────────────────────────────

class StateStore:
    """Dapr state store wrapper for save/get/delete operations."""

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

    def delete(self, key: str) -> None:
        """Delete a value from the Dapr state store."""
        with DaprClient() as client:
            client.delete_state(
                store_name=self.store_name, key=key
            )

    def bulk_get(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from the Dapr state store."""
        with DaprClient() as client:
            items = client.get_bulk_state(
                store_name=self.store_name, keys=keys
            )
            result = {}
            for item in items.items:
                if item.data:
                    result[item.key] = json.loads(item.data)
            return result


# ── T021: Secrets retrieval ───────────────────────────────────

class SecretStore:
    """Dapr secrets store wrapper."""

    def __init__(self, store_name: str = DAPR_SECRET_STORE):
        self.store_name = store_name

    def get_secret(self, secret_name: str, key: str) -> str:
        """Retrieve a secret value from the Dapr secret store."""
        with DaprClient() as client:
            secret = client.get_secret(
                store_name=self.store_name,
                key=secret_name,
            )
            return secret.secret[key]
