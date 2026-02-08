# Data Model: Advanced Cloud Deployment

**Branch**: `001-advanced-cloud-deployment`
**Date**: 2026-02-08

## Entities

### Task

Primary entity representing a user's to-do item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique task identifier |
| title | string (max 255) | Yes | Task title |
| description | string (max 2000) | No | Task description |
| status | enum | Yes | pending, completed, deleted |
| priority | enum | No | high, medium, low (default: medium) |
| due_date | datetime (ISO 8601) | No | Task due date |
| tags | string[] | No | List of tag names (default: []) |
| recurrence_pattern | enum | No | daily, weekly, monthly, null |
| recurrence_parent_id | UUID | No | Links to original recurring task series |
| created_by | string | Yes | User ID who created the task |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

**Validation Rules**:
- title MUST NOT be empty or whitespace-only
- status MUST be one of: pending, completed, deleted
- priority MUST be one of: high, medium, low (if provided)
- recurrence_pattern MUST be one of: daily, weekly, monthly
  (if provided)
- due_date MUST be a valid ISO 8601 datetime (if provided)
- tags entries MUST be non-empty strings, max 50 chars each,
  max 20 tags per task

**State Transitions**:
```
pending → completed  (mark complete)
pending → deleted    (delete)
completed → pending  (reopen — optional)
```

### TaskEvent

Immutable event record for task lifecycle actions. Published to
`task-events` Kafka topic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | UUID | Yes | Unique event identifier |
| event_type | enum | Yes | task.created, task.updated, task.completed, task.deleted |
| task_id | UUID | Yes | Reference to the task |
| payload | object | Yes | Event-specific data (see below) |
| user_id | string | Yes | User who triggered the action |
| timestamp | datetime | Yes | When the event occurred |

**Payload schemas by event_type**:

- `task.created`: `{ task: <full Task object> }`
- `task.updated`: `{ task_id, changes: { field: { old, new } } }`
- `task.completed`: `{ task_id, completed_at, recurrence_pattern }`
- `task.deleted`: `{ task_id, deleted_at }`

### Reminder

Scheduled notification trigger managed via Dapr Jobs API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reminder_id | UUID | Yes | Unique reminder identifier |
| task_id | UUID | Yes | Reference to the task |
| scheduled_time | datetime | Yes | When to fire the reminder |
| status | enum | Yes | pending, sent, cancelled |
| created_at | datetime | Yes | When the reminder was created |

**State Transitions**:
```
pending → sent       (reminder fires and notification delivered)
pending → cancelled  (task completed, deleted, or due date changed)
```

### Notification

Message delivered to a user. Published to `reminders` Kafka topic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| notification_id | UUID | Yes | Unique notification identifier |
| reminder_id | UUID | Yes | Reference to the reminder |
| user_id | string | Yes | Recipient user |
| channel | enum | Yes | push, email |
| delivery_status | enum | Yes | pending, delivered, failed |
| message | string | Yes | Notification message text |
| sent_at | datetime | No | When actually delivered |
| created_at | datetime | Yes | When created |

### AuditLogEntry

Persisted record consumed by the Audit Service from
`task-events` topic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| log_id | UUID | Yes | Unique log entry identifier |
| event_id | UUID | Yes | Reference to the original TaskEvent |
| event_type | string | Yes | Echoed from TaskEvent |
| task_id | UUID | Yes | Reference to the task |
| payload | object | Yes | Full event payload (stored as JSON) |
| user_id | string | Yes | User who triggered the action |
| event_timestamp | datetime | Yes | Original event timestamp |
| received_at | datetime | Yes | When the Audit Service received it |

## Relationships

```
Task (1) ──── (0..*) TaskEvent       [task lifecycle events]
Task (1) ──── (0..1) Reminder        [at most one active reminder]
Task (1) ──── (0..*) Task            [recurrence: parent → children via recurrence_parent_id]
Reminder (1) ── (0..1) Notification  [reminder triggers notification]
TaskEvent (1) ── (1) AuditLogEntry   [every event is audit-logged]
```

## Dapr State Store Keys

Tasks are stored in the Dapr state store with the following
key patterns:

| Key Pattern | Value | Description |
|-------------|-------|-------------|
| `task:{task_id}` | Task JSON | Individual task state |
| `tasks:user:{user_id}` | Task ID list | Index of tasks by user |
| `reminder:{reminder_id}` | Reminder JSON | Active reminder state |
| `conversation:{session_id}` | Conversation JSON | Chat conversation state |
