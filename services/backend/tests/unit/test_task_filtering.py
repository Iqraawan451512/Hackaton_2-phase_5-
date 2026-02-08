# [Task]: T063 — Unit tests for TaskService filter/sort/search
"""Tests for TaskService.list_tasks() filtering, sorting, and search."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.models.task import TaskCreate, TaskPriority, RecurrencePattern
from src.services.task_service import TaskService


@pytest.fixture
def mock_store():
    """Create a mock StateStore backed by a dict."""
    store = MagicMock()
    data = {}

    def save(key, value):
        data[key] = value

    def get(key):
        return data.get(key)

    def bulk_get(keys):
        return {k: data[k] for k in keys if k in data}

    store.save.side_effect = save
    store.get.side_effect = get
    store.bulk_get.side_effect = bulk_get
    store._data = data
    return store


@pytest.fixture
def mock_publisher():
    return MagicMock()


@pytest.fixture
def service(mock_store, mock_publisher):
    return TaskService(state_store=mock_store, publisher=mock_publisher)


@pytest.fixture
def seeded_service(service):
    """Service with pre-created tasks for filtering tests."""
    service.create(
        TaskCreate(
            title="Buy groceries",
            priority=TaskPriority.HIGH,
            tags=["shopping", "personal"],
        ),
        "user-1",
    )
    service.create(
        TaskCreate(
            title="Write report",
            priority=TaskPriority.MEDIUM,
            tags=["work"],
        ),
        "user-1",
    )
    service.create(
        TaskCreate(
            title="Buy milk",
            priority=TaskPriority.LOW,
            tags=["shopping"],
        ),
        "user-1",
    )
    return service


class TestSearch:
    """Tests for title search."""

    def test_search_by_title(self, seeded_service):
        results = seeded_service.list_tasks("user-1", search="buy")
        assert len(results) == 2

    def test_search_case_insensitive(self, seeded_service):
        results = seeded_service.list_tasks("user-1", search="REPORT")
        assert len(results) == 1
        assert results[0].title == "Write report"

    def test_search_no_match(self, seeded_service):
        results = seeded_service.list_tasks("user-1", search="xyz")
        assert len(results) == 0


class TestFilterByPriority:
    """Tests for priority filtering."""

    def test_filter_high(self, seeded_service):
        results = seeded_service.list_tasks("user-1", priority="high")
        assert len(results) == 1
        assert results[0].priority == TaskPriority.HIGH

    def test_filter_low(self, seeded_service):
        results = seeded_service.list_tasks("user-1", priority="low")
        assert len(results) == 1


class TestFilterByTag:
    """Tests for tag filtering."""

    def test_filter_by_tag(self, seeded_service):
        results = seeded_service.list_tasks("user-1", tag="shopping")
        assert len(results) == 2

    def test_filter_by_work_tag(self, seeded_service):
        results = seeded_service.list_tasks("user-1", tag="work")
        assert len(results) == 1
        assert results[0].title == "Write report"


class TestSorting:
    """Tests for sort_by and sort_order."""

    def test_sort_by_priority_asc(self, seeded_service):
        results = seeded_service.list_tasks(
            "user-1", sort_by="priority", sort_order="asc"
        )
        assert results[0].priority == TaskPriority.HIGH
        assert results[-1].priority == TaskPriority.LOW

    def test_sort_by_priority_desc(self, seeded_service):
        results = seeded_service.list_tasks(
            "user-1", sort_by="priority", sort_order="desc"
        )
        assert results[0].priority == TaskPriority.LOW
        assert results[-1].priority == TaskPriority.HIGH

    def test_sort_by_title_asc(self, seeded_service):
        results = seeded_service.list_tasks(
            "user-1", sort_by="title", sort_order="asc"
        )
        assert results[0].title == "Buy groceries"

    def test_default_sort_is_created_at_desc(self, seeded_service):
        results = seeded_service.list_tasks("user-1")
        # Last created should be first (desc)
        assert results[0].title == "Buy milk"


class TestCombinedFilters:
    """Tests for combining search, filter, and sort."""

    def test_search_and_priority(self, seeded_service):
        results = seeded_service.list_tasks(
            "user-1", search="buy", priority="high"
        )
        assert len(results) == 1
        assert results[0].title == "Buy groceries"

    def test_tag_and_sort(self, seeded_service):
        results = seeded_service.list_tasks(
            "user-1",
            tag="shopping",
            sort_by="priority",
            sort_order="asc",
        )
        assert len(results) == 2
        assert results[0].priority == TaskPriority.HIGH
