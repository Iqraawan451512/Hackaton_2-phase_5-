# [Task]: T028-T032, T049, T057, T059 — Backend API task endpoints
"""Task API endpoints for the Backend Service."""

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional

from src.config import STANDALONE_MODE
from src.models.task import Task, TaskCreate, TaskUpdate
from src.services.task_service import TaskService

if STANDALONE_MODE:
    from src.standalone import (
        MemoryEventPublisher,
        MemoryReminderScheduler,
        MemoryStateStore,
    )
else:
    from src.services.reminder_scheduler import ReminderScheduler

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Service instances (overridable via dependency injection in tests)
_service: Optional[TaskService] = None
_scheduler = None


def get_service() -> TaskService:
    """Get or create the TaskService singleton."""
    global _service
    if _service is None:
        if STANDALONE_MODE:
            store = MemoryStateStore()
            publisher = MemoryEventPublisher()
            _service = TaskService(state_store=store, publisher=publisher)
        else:
            _service = TaskService()
    return _service


def get_scheduler():
    """Get or create the ReminderScheduler singleton."""
    global _scheduler
    if _scheduler is None:
        if STANDALONE_MODE:
            _scheduler = MemoryReminderScheduler()
        else:
            _scheduler = ReminderScheduler()
    return _scheduler


# ── T028: POST /api/tasks ────────────────────────────────────

@router.post("", status_code=201, response_model=Task)
async def create_task(
    data: TaskCreate,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> Task:
    """Create a new task. Publishes task.created event.
    Schedules a reminder if due_date is set."""
    service = get_service()
    task = service.create(data, x_user_id)
    if task.due_date:
        scheduler = get_scheduler()
        scheduler.schedule(task.id, task.due_date)
    return task


# ── T029: GET /api/tasks and GET /api/tasks/{id} ─────────────

@router.get("", response_model=list[Task])
async def list_tasks(
    x_user_id: str = Header(..., alias="X-User-ID"),
    search: Optional[str] = Query(None, description="Search by title"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort direction"),
) -> list[Task]:
    """List tasks with optional filtering, sorting, and search."""
    service = get_service()
    return service.list_tasks(
        user_id=x_user_id,
        search=search,
        priority=priority,
        tag=tag,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    """Get a single task by ID."""
    service = get_service()
    task = service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── T030: PATCH /api/tasks/{id} ──────────────────────────────

@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> Task:
    """Update a task. Publishes task.updated event.
    Reschedules reminder if due_date changed."""
    service = get_service()
    task = service.update(task_id, data, x_user_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if data.due_date is not None:
        scheduler = get_scheduler()
        if task.due_date:
            scheduler.schedule(task.id, task.due_date)
        else:
            scheduler.cancel(task.id)
    return task


# ── T031: DELETE /api/tasks/{id} ──────────────────────────────

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> None:
    """Soft-delete a task. Publishes task.deleted event. Cancels reminder."""
    service = get_service()
    scheduler = get_scheduler()
    scheduler.cancel(task_id)
    deleted = service.delete(task_id, x_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")


# ── T032: POST /api/tasks/{id}/complete ───────────────────────

@router.post("/{task_id}/complete", response_model=Task)
async def complete_task(
    task_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> Task:
    """Mark a task as completed. Publishes task.completed event. Cancels reminder."""
    service = get_service()
    scheduler = get_scheduler()
    scheduler.cancel(task_id)
    task = service.complete(task_id, x_user_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── T059: PUT /api/tasks/{id}/tags ────────────────────────────

class TagsBody(BaseModel):
    """Request body for replacing task tags."""
    tags: list[str]


@router.put("/{task_id}/tags", response_model=Task)
async def update_tags(
    task_id: str,
    body: TagsBody,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> Task:
    """Replace all tags on a task."""
    service = get_service()
    task = service.update(
        task_id,
        TaskUpdate(tags=body.tags),
        x_user_id,
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
