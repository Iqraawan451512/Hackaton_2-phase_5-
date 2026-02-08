# [Task]: T040 — Recurring Task Service configuration
"""Configuration for the Recurring Task Service."""

import logging
import sys

import structlog

DAPR_PUBSUB_NAME = "kafka-pubsub"
BACKEND_APP_ID = "backend"


def configure_logging(
    service_name: str = "recurring-task",
) -> None:
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


def get_logger(
    name: str = "recurring-task",
) -> structlog.BoundLogger:
    """Get a named structured logger."""
    return structlog.get_logger(service=name)
