# Feature Specification: Advanced Cloud Deployment

**Feature Branch**: `001-advanced-cloud-deployment`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "Todo Chatbot Phase V — Advanced Features, Event-driven Architecture, Dapr Integration, Kafka, Minikube & Cloud Deployment"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Task Event Publishing (Priority: P1)

As a system operator, I want every task CRUD operation to produce
an event so that downstream services (audit, notifications,
real-time sync) can react without direct coupling.

**Why this priority**: This is the foundational event-driven
infrastructure. All other stories (recurring tasks, reminders,
real-time sync, audit) depend on events flowing through the
message broker. Without this, no downstream service can function.

**Independent Test**: Create, update, complete, and delete a task
via the Chat API. Verify that each operation produces a correctly
structured event on the `task-events` topic and that the Audit
Service consumes and persists each event.

**Acceptance Scenarios**:

1. **Given** a user creates a new task, **When** the backend
   processes the request, **Then** a `task.created` event is
   published to `task-events` containing the task ID, title,
   timestamp, and user ID.
2. **Given** a user updates a task's title or description,
   **When** the update is saved, **Then** a `task.updated` event
   is published to `task-events` with old and new values.
3. **Given** a user marks a task as complete, **When** the
   completion is processed, **Then** a `task.completed` event is
   published to `task-events`.
4. **Given** a user deletes a task, **When** the deletion is
   processed, **Then** a `task.deleted` event is published to
   `task-events`.
5. **Given** any task event is published, **When** the Audit
   Service receives it, **Then** the event is stored with full
   payload, timestamp, and event type for audit trail.

---

### User Story 2 - Recurring Tasks (Priority: P2)

As a user, I want to create recurring tasks (daily, weekly,
monthly) so that I do not need to manually recreate them.

**Why this priority**: Recurring tasks are the most requested
advanced feature and showcase the event-driven architecture
end-to-end. They build directly on the task event foundation.

**Independent Test**: Create a recurring daily task. Mark it
complete. Verify the system automatically creates the next
instance with the correct due date and that events are emitted
for both the completion and the new task creation.

**Acceptance Scenarios**:

1. **Given** a user creates a task with recurrence "daily",
   **When** the task is saved, **Then** the first task instance
   is created with a due date of today.
2. **Given** a user creates a task with recurrence "weekly",
   **When** the task is saved, **Then** the first task instance
   is created with a due date of today, and the recurrence
   pattern is stored.
3. **Given** a user creates a task with recurrence "monthly",
   **When** the task is saved, **Then** the first task instance
   is created with a due date of today, and the recurrence
   pattern is stored.
4. **Given** a recurring task is marked complete, **When** the
   completion is processed, **Then** the next task instance is
   automatically created with the due date advanced by the
   recurrence interval.
5. **Given** a recurring task event fires, **When** the Audit
   Service receives the event, **Then** both the completion and
   new-instance-creation events are logged.

---

### User Story 3 - Due Dates & Reminders (Priority: P3)

As a user, I want to set a due date on a task and receive
reminders so that I never miss a deadline.

**Why this priority**: Due dates and reminders are essential for
task management and drive the Notification Service, which is a
key microservice in the architecture.

**Independent Test**: Create a task with a due date 5 minutes
from now. Verify a reminder notification is delivered at the
correct time via the Notification Service.

**Acceptance Scenarios**:

1. **Given** a user creates or edits a task, **When** they set a
   due date, **Then** the due date is persisted and visible in
   the task view.
2. **Given** a task has a due date, **When** the reminder time
   arrives, **Then** a reminder event is published to the
   `reminders` topic.
3. **Given** a reminder event is published, **When** the
   Notification Service receives it, **Then** a notification is
   sent to the user (push or email).
4. **Given** a user modifies a task's due date, **When** the
   update is saved, **Then** the previously scheduled reminder
   is cancelled and a new one is scheduled for the updated date.
5. **Given** a task is completed before the due date, **When**
   completion is processed, **Then** any pending reminder for
   that task is cancelled.

---

### User Story 4 - Priority, Tags, Search, Filter, Sort (Priority: P4)

As a user, I want to organize my tasks by priority and tags, and
search, filter, and sort them so that I can find what I need
quickly.

**Why this priority**: Task organization enhances usability but
is not a prerequisite for the event-driven or deployment
infrastructure. It can be built independently.

**Independent Test**: Create several tasks with different
priorities and tags. Use search, filter, and sort controls in the
frontend to verify correct behavior.

**Acceptance Scenarios**:

1. **Given** a user creates or edits a task, **When** they assign
   a priority (High, Medium, Low), **Then** the priority is
   persisted and displayed in the task view.
2. **Given** a user creates or edits a task, **When** they add
   one or more tags, **Then** the tags are persisted and
   displayed on the task.
3. **Given** a user edits a task's tags, **When** they remove a
   tag, **Then** the tag is removed from the task.
4. **Given** a list of tasks with varying priorities, **When** the
   user sorts by priority, **Then** tasks are ordered
   High > Medium > Low (or reverse).
5. **Given** a list of tasks with tags, **When** the user filters
   by a specific tag, **Then** only tasks with that tag are
   displayed.
6. **Given** a list of tasks, **When** the user enters a search
   query, **Then** tasks matching the query in title or
   description are displayed.

---

### User Story 5 - Real-Time Client Sync (Priority: P5)

As a user with multiple devices or sessions open, I want task
updates to appear in real-time across all my connected clients so
that I always see the latest state.

**Why this priority**: Real-time sync improves UX but depends on
the task event pipeline (US1) being in place first. It is an
enhancement layer.

**Independent Test**: Open two browser tabs. Create or update a
task in one tab. Verify the change appears in the other tab
within 2 seconds without manual refresh.

**Acceptance Scenarios**:

1. **Given** a user has two clients connected, **When** a task is
   created on client A, **Then** client B sees the new task
   within 2 seconds.
2. **Given** a user has two clients connected, **When** a task is
   updated on client A, **Then** client B reflects the updated
   task within 2 seconds.
3. **Given** a user has two clients connected, **When** a task is
   deleted on client A, **Then** client B removes the task from
   view within 2 seconds.
4. **Given** a task update event is published to `task-updates`,
   **When** a WebSocket-connected client receives it, **Then**
   the client UI updates without a page refresh.

---

### User Story 6 - Local Deployment on Minikube (Priority: P6)

As a developer, I want to deploy all services to Minikube with
Dapr sidecars so that I can develop and test the full
microservices architecture locally.

**Why this priority**: Local deployment validates the
architecture end-to-end and is a prerequisite for cloud
deployment. However, the application features (US1–US5) must
be built first to have something to deploy.

**Independent Test**: Run `minikube start`, deploy all services
via Helm charts, and verify that task creation flows through
the event pipeline, reminders fire, and real-time sync works.

**Acceptance Scenarios**:

1. **Given** Minikube is running, **When** Helm charts are
   applied, **Then** all services (Frontend, Backend, Notification,
   Recurring Task, Audit) start with Dapr sidecars attached.
2. **Given** all services are running on Minikube, **When** a
   user creates a task via the frontend, **Then** the event flows
   through Dapr Pub/Sub to Kafka and is received by the Audit
   Service.
3. **Given** Dapr components are configured, **When** the
   application accesses state, secrets, or scheduled jobs,
   **Then** all operations succeed through the Dapr sidecar
   without direct DB or Kafka connections.
4. **Given** Kafka runs on Minikube, **Then** it uses at most
   1 replica of Kafka and 1 replica of Zookeeper.

---

### User Story 7 - Cloud Deployment (Priority: P7)

As a DevOps engineer, I want to deploy all services to a cloud
Kubernetes cluster (GKE, AKS, or OKE) with automated CI/CD so
that the application runs in a production-grade environment.

**Why this priority**: Cloud deployment is the final milestone
and depends on all features and local deployment being validated
first.

**Independent Test**: Push a commit to the main branch. Verify
that GitHub Actions builds, tests, and deploys all services to
the cloud cluster, and that end-to-end event-driven features
work correctly.

**Acceptance Scenarios**:

1. **Given** a commit is pushed to the main branch, **When**
   GitHub Actions CI/CD triggers, **Then** all services are
   built, tested, and deployed to the cloud cluster.
2. **Given** all services are deployed to cloud K8s, **When**
   a user creates a task, **Then** the full event pipeline
   (task-events, reminders, task-updates) operates correctly.
3. **Given** a cloud deployment, **Then** each service runs
   with at least 2 replicas for high availability.
4. **Given** a cloud deployment, **When** a service pod fails,
   **Then** Kubernetes restarts it and the Dapr sidecar
   reconnects without data loss.

---

### Edge Cases

- What happens when a recurring task is deleted before completion?
  The recurrence chain stops; no future instances are created.
- What happens when two clients update the same task
  simultaneously? The last-write-wins policy applies; both
  clients receive the final state via real-time sync.
- What happens when the Notification Service is down when a
  reminder fires? The event remains on the `reminders` Kafka
  topic and is consumed when the service recovers (at-least-once
  delivery).
- What happens when a due date is set in the past? The system
  immediately publishes a reminder event so the user is notified
  that the task is overdue.
- What happens when Kafka is temporarily unavailable? Service
  producers retry via Dapr Pub/Sub retry policy. Events are not
  lost due to Kafka's persistence guarantees once available.
- What happens when a user assigns an empty tag list? The task
  is saved with no tags; filter-by-tag excludes it from
  tag-specific views.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST publish a structured event to the
  `task-events` Kafka topic for every task create, update,
  complete, and delete operation.
- **FR-002**: System MUST support creating tasks with a
  recurrence pattern of daily, weekly, or monthly.
- **FR-003**: System MUST automatically create the next task
  instance when a recurring task is marked complete, advancing
  the due date by the recurrence interval.
- **FR-004**: System MUST allow users to set and modify due
  dates on tasks.
- **FR-005**: System MUST schedule reminders via the Dapr Jobs
  API and publish reminder events to the `reminders` Kafka topic
  at the correct time.
- **FR-006**: Notification Service MUST consume the `reminders`
  topic and deliver notifications to users.
- **FR-007**: System MUST support assigning a priority (High,
  Medium, Low) to each task.
- **FR-008**: System MUST support adding, editing, and removing
  multiple tags per task.
- **FR-009**: Frontend MUST provide search, filter (by tag,
  priority, status), and sort (by priority, due date, creation
  date) capabilities.
- **FR-010**: System MUST broadcast task updates to all connected
  clients via the `task-updates` Kafka topic and WebSocket
  connections within 2 seconds.
- **FR-011**: Audit Service MUST consume and persist all events
  from `task-events` for a complete audit trail.
- **FR-012**: All inter-service communication MUST use Dapr
  Pub/Sub; no direct Kafka or DB connections in service code.
- **FR-013**: All state access MUST use the Dapr state store
  abstraction.
- **FR-014**: All secrets MUST be retrieved via the Dapr Secrets
  API or Kubernetes Secrets.
- **FR-015**: All services MUST be containerized with Docker and
  deployable via Helm charts to Minikube and cloud Kubernetes.
- **FR-016**: CI/CD pipelines MUST be implemented with GitHub
  Actions for automated build, test, and deploy.
- **FR-017**: Each service MUST emit structured logs for
  observability.

### Key Entities

- **Task**: Represents a user's to-do item. Attributes: ID,
  title, description, status (pending/completed/deleted),
  priority (High/Medium/Low), due date, tags, recurrence
  pattern, created-by user ID, timestamps.
- **Recurring Task Template**: Defines the recurrence rule
  (daily/weekly/monthly) and links to the parent task series.
  Each completion spawns the next Task instance.
- **Task Event**: An immutable record of a task lifecycle action.
  Attributes: event ID, event type (created/updated/completed/
  deleted), task ID, payload (before/after state), timestamp,
  user ID.
- **Reminder**: A scheduled notification trigger. Attributes:
  reminder ID, task ID, scheduled time, status (pending/sent/
  cancelled).
- **Notification**: A message delivered to a user. Attributes:
  notification ID, reminder ID, channel (push/email), delivery
  status, timestamp.
- **Tag**: A user-defined label attached to tasks for
  categorization. Attributes: tag name, associated task IDs.
- **Audit Log Entry**: A persisted event consumed by the Audit
  Service. Attributes: log ID, event type, full event payload,
  received timestamp.

### Assumptions

- The existing Phase IV frontend and backend provide the base
  task CRUD functionality; Phase V extends it with events,
  recurrence, reminders, priority, tags, and deployment.
- Notification delivery channel defaults to in-app push
  notifications. Email delivery is a stretch goal.
- Reminder lead time defaults to 30 minutes before due date
  unless the user specifies otherwise.
- The WebSocket connection for real-time sync is managed per
  browser session; no mobile-specific push is required in scope.
- Kafka message retention defaults to 7 days for all topics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of task CRUD operations produce a
  corresponding event within 1 second of the operation.
- **SC-002**: 100% of recurring task completions trigger
  automatic creation of the next instance within 5 seconds.
- **SC-003**: 100% of due-date reminders are delivered to the
  user within 60 seconds of the scheduled time.
- **SC-004**: Audit logs capture every task event with zero
  data loss over a 24-hour period.
- **SC-005**: Real-time sync updates appear on all connected
  clients within 2 seconds of the originating action.
- **SC-006**: Users can search, filter, and sort tasks with
  results appearing within 1 second.
- **SC-007**: All services deploy successfully to Minikube with
  Dapr sidecars and pass end-to-end smoke tests.
- **SC-008**: All services deploy successfully to a cloud
  Kubernetes cluster via GitHub Actions CI/CD and pass
  end-to-end smoke tests.
- **SC-009**: Each service in the cloud deployment runs with at
  least 2 replicas and recovers from a single pod failure
  without user-visible downtime.
