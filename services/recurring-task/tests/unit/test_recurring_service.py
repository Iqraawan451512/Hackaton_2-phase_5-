# [Task]: T045 — Unit tests for RecurringTaskService
"""Tests for RecurringTaskService date computation and logic."""

from datetime import datetime, timedelta, timezone

import pytest

from src.services.recurring_service import compute_next_due_date


class TestComputeNextDueDate:
    """Tests for the compute_next_due_date function."""

    def test_daily_recurrence(self):
        base = datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc)
        result = compute_next_due_date("daily", from_date=base)
        expected = datetime(2026, 2, 9, 12, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_weekly_recurrence(self):
        base = datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc)
        result = compute_next_due_date("weekly", from_date=base)
        expected = datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_monthly_recurrence(self):
        base = datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc)
        result = compute_next_due_date("monthly", from_date=base)
        expected = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_monthly_handles_end_of_month(self):
        """January 31 → February should cap at day 28."""
        base = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)
        result = compute_next_due_date("monthly", from_date=base)
        assert result.month == 2
        assert result.day == 28

    def test_monthly_december_to_january(self):
        """December → January crosses year boundary."""
        base = datetime(2026, 12, 15, 12, 0, tzinfo=timezone.utc)
        result = compute_next_due_date("monthly", from_date=base)
        assert result.year == 2027
        assert result.month == 1
        assert result.day == 15

    def test_daily_crosses_month_boundary(self):
        base = datetime(2026, 2, 28, 23, 0, tzinfo=timezone.utc)
        result = compute_next_due_date("daily", from_date=base)
        assert result.month == 3
        assert result.day == 1

    def test_unknown_pattern_raises(self):
        with pytest.raises(ValueError, match="Unknown recurrence"):
            compute_next_due_date("yearly")

    def test_defaults_to_now(self):
        """When no from_date provided, should use approximately now."""
        before = datetime.now(timezone.utc)
        result = compute_next_due_date("daily")
        after = datetime.now(timezone.utc) + timedelta(days=1, seconds=1)
        assert before + timedelta(days=1) <= result <= after
