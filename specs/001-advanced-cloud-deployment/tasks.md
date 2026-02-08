# Tasks: Advanced Cloud Deployment

**Input**: Design documents from `/specs/001-advanced-cloud-deployment/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests required per constitution (Development Standards §Testing). Integration tests required for event-driven behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Kafka cluster, Dapr components, and base project structure

- [x] T001 Create project directory structure per plan.md layout in services/backend/, services/notification/, services/recurring-task/, services/audit/, services/frontend/, deploy/
- [x] T002 [P] Initialize Backend Service Python project with FastAPI + Dapr SDK dependencies in services/backend/requirements.txt
- [x] T003 [P] Initialize Notification Service Python project with FastAPI + Dapr SDK dependencies in services/notification/requirements.txt
- [x] T004 [P] Initialize Recurring Task Service Python project with FastAPI + Dapr SDK dependencies in services/recurring-task/requirements.txt
- [x] T005 [P] Initialize Audit Service Python project with FastAPI + Dapr SDK dependencies in services/audit/requirements.txt
- [x] T006 [P] Initialize Frontend Service Next.js project with TypeScript + Dapr JS SDK in services/frontend/package.json
- [x] T007 [P] Configure Python linting (PEP 8 / ruff) and formatting in services/backend/pyproject.toml
- [x] T008 [P] Configure Frontend linting (ESLint + Prettier) in services/frontend/.eslintrc.json and services/frontend/.prettierrc
- [x] T009 Create Kafka cluster manifest for Minikube (Redpanda, 1 replica) with topics task-events, reminders, task-updates in deploy/helm/kafka/values.yaml
- [x] T010 [P] Create Dapr Pub/Sub component definition (pubsub.kafka) in deploy/dapr/pubsub.yaml
- [x] T011 [P] Create Dapr state store component definition (state.postgresql, Neon DB) in deploy/dapr/statestore.yaml
- [x] T012 [P] Create Dapr secrets store component definition (secretstores.kubernetes) in deploy/dapr/secrets.yaml
- [x] T013 [P] Create Dapr Jobs component definition in deploy/dapr/jobs.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, Dapr client wrappers, and shared event schemas that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T014 Create Task model with all fields (id, title, description, status, priority, due_date, tags, recurrence_pattern, recurrence_parent_id, created_by, timestamps) and validation rules in services/backend/src/models/task.py
- [x] T015 [P] Create TaskEvent model (event_id, event_type, task_id, payload, user_id, timestamp) per contracts/task-events.json schema in services/backend/src/events/task_event.py
- [x] T016 [P] Create Reminder model (reminder_id, task_id, scheduled_time, status, created_at) in services/backend/src/models/reminder.py
- [x] T017 [P] Create Notification model (notification_id, reminder_id, user_id, channel, delivery_status, message, sent_at) in services/notification/src/models/notification.py
- [x] T018 [P] Create AuditLogEntry model (log_id, event_id, event_type, task_id, payload, user_id, event_timestamp, received_at) in services/audit/src/models/audit_log.py
- [x] T019 Implement Dapr client wrapper for state store operations (save, get, delete, bulk get) in services/backend/src/config.py
- [x] T020 [P] Implement Dapr client wrapper for Pub/Sub publishing (publish event to topic) in services/backend/src/events/publisher.py
- [x] T021 [P] Implement Dapr client wrapper for secrets retrieval in services/backend/src/config.py (extend)
- [x] T022 Implement structured logging configuration (JSON format) reusable across all Python services in services/backend/src/config.py (extend)
- [x] T023 Create FastAPI application skeleton with health check endpoint in services/backend/src/api/__init__.py
- [x] T024 [P] Create unit tests for Task model validation rules in services/backend/tests/unit/test_task_model.py
- [x] T025 [P] Create unit tests for TaskEvent model in services/backend/tests/unit/test_task_event.py

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Task Event Publishing (Priority: P1) MVP

**Goal**: Every task CRUD operation produces a structured event to `task-events` topic; Audit Service consumes and stores events.

**Independent Test**: Create, update, complete, and delete a task via the Backend API. Verify each operation publishes the correct event to `task-events` and the Audit Service persists each event.

### Implementation for User Story 1

- [x] T026 [US1] Implement TaskService with CRUD operations (create, get, list, update, delete, complete) using Dapr state store in services/backend/src/services/task_service.py
- [x] T027 [US1] Implement EventPublisher.publish_task_event() to publish task.created/updated/completed/deleted events to task-events topic via Dapr Pub/Sub in services/backend/src/events/publisher.py (extend)
- [x] T028 [US1] Implement POST /api/tasks endpoint (create task, publish task.created event) in services/backend/src/api/tasks.py
- [x] T029 [US1] Implement GET /api/tasks and GET /api/tasks/{id} endpoints in services/backend/src/api/tasks.py (extend)
- [x] T030 [US1] Implement PATCH /api/tasks/{id} endpoint (update task, publish task.updated event) in services/backend/src/api/tasks.py (extend)
- [x] T031 [US1] Implement DELETE /api/tasks/{id} endpoint (delete task, publish task.deleted event) in services/backend/src/api/tasks.py (extend)
- [x] T032 [US1] Implement POST /api/tasks/{id}/complete endpoint (mark complete, publish task.completed event) in services/backend/src/api/tasks.py (extend)
- [x] T033 [US1] Implement Audit Service FastAPI app with Dapr subscription to task-events topic in services/audit/src/handlers/task_events.py
- [x] T034 [US1] Implement AuditLogService to persist AuditLogEntry to Dapr state store in services/audit/src/services/audit_service.py
- [x] T035 [US1] Add structured logging for all task CRUD operations in services/backend/src/services/task_service.py (extend)
- [x] T036 [P] [US1] Create unit tests for TaskService CRUD operations in services/backend/tests/unit/test_task_service.py
- [x] T037 [P] [US1] Create unit tests for EventPublisher in services/backend/tests/unit/test_event_publisher.py
- [x] T038 [P] [US1] Create unit tests for AuditLogService in services/audit/tests/unit/test_audit_service.py
- [x] T039 [US1] Create integration test: task CRUD → event published → Audit Service receives and stores in services/backend/tests/integration/test_task_events_flow.py

**Checkpoint**: Task CRUD + event publishing + audit logging fully functional and testable independently

---

## Phase 4: User Story 2 — Recurring Tasks (Priority: P2)

**Goal**: Users can create recurring tasks (daily/weekly/monthly); completing a recurring task auto-creates the next instance.

**Independent Test**: Create a recurring daily task. Mark it complete. Verify the next instance is auto-created with the correct due date and both events are audit-logged.

### Implementation for User Story 2

- [x] T040 [US2] Implement Recurring Task Service FastAPI app with Dapr subscription to task-events topic (filter for task.completed events) in services/recurring-task/src/handlers/task_events.py
- [x] T041 [US2] Implement RecurringTaskService logic: check recurrence_pattern, compute next due date, create next task via Dapr Service Invocation to Backend in services/recurring-task/src/services/recurring_service.py
- [x] T042 [US2] Extend POST /api/tasks to accept recurrence_pattern (daily/weekly/monthly) and store it on the Task in services/backend/src/api/tasks.py (extend)
- [x] T043 [US2] Extend task.completed event payload to include recurrence_pattern field in services/backend/src/events/publisher.py (extend)
- [x] T044 [US2] Add structured logging for recurring task creation in services/recurring-task/src/services/recurring_service.py (extend)
- [x] T045 [P] [US2] Create unit tests for RecurringTaskService (daily/weekly/monthly date computation) in services/recurring-task/tests/unit/test_recurring_service.py
- [x] T046 [US2] Create integration test: complete recurring task → next instance created → events audit-logged in services/recurring-task/tests/integration/test_recurring_flow.py

**Checkpoint**: Recurring tasks fully functional — completing a recurring task auto-creates the next instance

---

## Phase 5: User Story 3 — Due Dates & Reminders (Priority: P3)

**Goal**: Users can set due dates on tasks and receive reminder notifications via the Notification Service.

**Independent Test**: Create a task with a due date. Verify a reminder is scheduled via Dapr Jobs and the Notification Service delivers a notification when the reminder fires.

### Implementation for User Story 3

- [x] T047 [US3] Implement ReminderScheduler to schedule/cancel reminders via Dapr Jobs API (schedule at due_date minus 30 min) in services/backend/src/services/reminder_scheduler.py
- [x] T048 [US3] Implement POST /api/jobs/trigger callback endpoint to handle Dapr Jobs firing — publish reminder event to reminders topic in services/backend/src/api/jobs.py
- [x] T049 [US3] Extend POST /api/tasks and PATCH /api/tasks/{id} to call ReminderScheduler when due_date is set/changed in services/backend/src/api/tasks.py (extend)
- [x] T050 [US3] Implement reminder cancellation when task is completed or deleted in services/backend/src/services/reminder_scheduler.py (extend)
- [x] T051 [US3] Implement Notification Service FastAPI app with Dapr subscription to reminders topic in services/notification/src/handlers/reminders.py
- [x] T052 [US3] Implement NotificationService to deliver push notifications to users in services/notification/src/services/notification_service.py
- [x] T053 [US3] Add structured logging for reminder scheduling and notification delivery in services/notification/src/services/notification_service.py (extend)
- [x] T054 [P] [US3] Create unit tests for ReminderScheduler (schedule, cancel, reschedule) in services/backend/tests/unit/test_reminder_scheduler.py
- [x] T055 [P] [US3] Create unit tests for NotificationService in services/notification/tests/unit/test_notification_service.py
- [x] T056 [US3] Create integration test: set due date → Dapr Job fires → reminder event → Notification Service delivers in services/notification/tests/integration/test_reminder_flow.py

**Checkpoint**: Due dates and reminders fully functional — notifications delivered on schedule

---

## Phase 6: User Story 4 — Priority, Tags, Search, Filter, Sort (Priority: P4)

**Goal**: Users can assign priority and tags to tasks, and search/filter/sort tasks in the frontend.

**Independent Test**: Create several tasks with different priorities and tags. Use the frontend to filter by tag, sort by priority, and search by title.

### Implementation for User Story 4

- [x] T057 [US4] Extend GET /api/tasks with query parameters: search, priority, tag, status, sort_by, sort_order per contracts/backend-api.yaml in services/backend/src/api/tasks.py (extend)
- [x] T058 [US4] Implement TaskService.list_tasks() with filtering, sorting, and search logic using Dapr state store queries in services/backend/src/services/task_service.py (extend)
- [x] T059 [US4] Implement PUT /api/tasks/{id}/tags endpoint for adding/removing tags in services/backend/src/api/tasks.py (extend)
- [x] T060 [US4] Implement frontend TaskFilterBar component (priority dropdown, tag filter, search input, sort controls) in services/frontend/src/components/TaskFilterBar.tsx
- [x] T061 [US4] Implement frontend API client methods for filtered/sorted task listing in services/frontend/src/services/api-client.ts
- [x] T062 [US4] Integrate TaskFilterBar with task list page, wire up filter/sort/search state in services/frontend/src/pages/index.tsx
- [x] T063 [P] [US4] Create unit tests for TaskService filter/sort/search logic in services/backend/tests/unit/test_task_filtering.py
- [x] T064 [P] [US4] Create unit tests for TaskFilterBar component in services/frontend/tests/TaskFilterBar.test.tsx

**Checkpoint**: Priority, tags, search, filter, sort fully functional in backend and frontend

---

## Phase 7: User Story 5 — Real-Time Client Sync (Priority: P5)

**Goal**: Task updates broadcast to all connected clients in real-time via WebSocket.

**Independent Test**: Open two browser tabs. Create/update a task in one tab. Verify the change appears in the other tab within 2 seconds.

### Implementation for User Story 5

- [x] T065 [US5] Implement Backend WebSocket endpoint for client connections and event relay in services/backend/src/api/websocket.py
- [x] T066 [US5] Implement Dapr subscription handler for task-updates topic to relay events to WebSocket clients in services/backend/src/events/task_updates_handler.py
- [x] T067 [US5] Extend EventPublisher to publish task-updates events (created/updated/completed/deleted with current task state) on every CRUD operation in services/backend/src/events/publisher.py (extend)
- [x] T068 [US5] Implement frontend WebSocket client hook (useRealtimeUpdates) for receiving and applying task updates in services/frontend/src/hooks/useRealtimeUpdates.ts
- [x] T069 [US5] Integrate useRealtimeUpdates hook with task list page to auto-refresh on incoming events in services/frontend/src/pages/index.tsx (extend)
- [x] T070 [P] [US5] Create unit tests for WebSocket relay logic in services/backend/tests/unit/test_websocket.py
- [x] T071 [US5] Create integration test: task update → task-updates topic → WebSocket → client receives within 2s in services/backend/tests/integration/test_realtime_sync.py

**Checkpoint**: Real-time sync fully functional across multiple connected clients

---

## Phase 8: User Story 6 — Local Deployment on Minikube (Priority: P6)

**Goal**: All services deploy to Minikube with Dapr sidecars and pass end-to-end smoke tests.

**Independent Test**: Run minikube start, deploy via Helm, verify task CRUD + events + reminders + real-time sync all work.

### Implementation for User Story 6

- [x] T072 [P] [US6] Create Dockerfile for Backend Service in services/backend/Dockerfile
- [x] T073 [P] [US6] Create Dockerfile for Notification Service in services/notification/Dockerfile
- [x] T074 [P] [US6] Create Dockerfile for Recurring Task Service in services/recurring-task/Dockerfile
- [x] T075 [P] [US6] Create Dockerfile for Audit Service in services/audit/Dockerfile
- [x] T076 [P] [US6] Create Dockerfile for Frontend Service in services/frontend/Dockerfile
- [x] T077 [P] [US6] Create Helm chart for Backend Service (deployment, service, Dapr annotations) in deploy/helm/backend/
- [x] T078 [P] [US6] Create Helm chart for Notification Service in deploy/helm/notification/
- [x] T079 [P] [US6] Create Helm chart for Recurring Task Service in deploy/helm/recurring-task/
- [x] T080 [P] [US6] Create Helm chart for Audit Service in deploy/helm/audit/
- [x] T081 [P] [US6] Create Helm chart for Frontend Service in deploy/helm/frontend/
- [x] T082 [US6] Create Minikube deployment script (start cluster, install Dapr, deploy Kafka, apply Dapr components, deploy all services) in deploy/minikube/deploy.sh
- [x] T083 [US6] Verify all pods running with 2/2 containers (app + Dapr sidecar) and smoke test end-to-end flow on Minikube

**Checkpoint**: All services deployed on Minikube with Dapr sidecars, end-to-end flow verified

---

## Phase 9: User Story 7 — Cloud Deployment (Priority: P7)

**Goal**: All services deploy to cloud Kubernetes (GKE/AKS/OKE) with automated CI/CD via GitHub Actions.

**Independent Test**: Push a commit to main. Verify GitHub Actions builds, tests, and deploys. Verify end-to-end event pipeline works in cloud.

### Implementation for User Story 7

- [x] T084 [US7] Create GitHub Actions CI workflow (build + test all services on PR) in .github/workflows/ci.yaml
- [x] T085 [US7] Create GitHub Actions CD workflow (build Docker images, push to registry, Helm upgrade to cloud cluster on merge to main) in .github/workflows/cd.yaml
- [x] T086 [US7] Create cloud deployment script (apply Dapr components, deploy Kafka via Strimzi/Redpanda Cloud, deploy all services with min 2 replicas) in deploy/cloud/deploy.sh
- [x] T087 [US7] Configure Helm values for cloud deployment (2+ replicas, cloud Kafka, production secrets) in deploy/helm/*/values-cloud.yaml
- [x] T088 [US7] Verify cloud deployment: all services running with 2+ replicas, end-to-end event pipeline functional, pod failure recovery

**Checkpoint**: Cloud deployment fully operational with CI/CD automation

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Monitoring, logging hardening, documentation, and final validation

- [x] T089 [P] Implement structured logging configuration for Notification Service in services/notification/src/config.py
- [x] T090 [P] Implement structured logging configuration for Recurring Task Service in services/recurring-task/src/config.py
- [x] T091 [P] Implement structured logging configuration for Audit Service in services/audit/src/config.py
- [x] T092 Run full end-to-end test suite: CRUD → events → recurring → reminders → real-time sync → audit across all services
- [x] T093 Validate quickstart.md smoke test procedure against deployed Minikube environment in specs/001-advanced-cloud-deployment/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 - Task Events (Phase 3)**: Depends on Foundational — BLOCKS US2, US3, US5
- **US2 - Recurring Tasks (Phase 4)**: Depends on US1 (needs task.completed events)
- **US3 - Reminders (Phase 5)**: Depends on US1 (needs event pipeline)
- **US4 - Priority/Tags/Search (Phase 6)**: Depends on Foundational only — can run parallel with US1
- **US5 - Real-Time Sync (Phase 7)**: Depends on US1 (needs task-updates publishing)
- **US6 - Minikube (Phase 8)**: Depends on US1–US5 completion (needs services to deploy)
- **US7 - Cloud (Phase 9)**: Depends on US6 (validates locally first)
- **Polish (Phase 10)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2). Foundation for US2, US3, US5.
- **US2 (P2)**: Depends on US1 (subscribes to task-events). Independent of US3, US4, US5.
- **US3 (P3)**: Depends on US1 (event pipeline). Independent of US2, US4, US5.
- **US4 (P4)**: Independent of US1–US3 — can start after Foundational. Only needs Task model.
- **US5 (P5)**: Depends on US1 (task-updates publishing). Independent of US2, US3, US4.
- **US6 (P6)**: Depends on all application user stories (US1–US5).
- **US7 (P7)**: Depends on US6 (local deployment validated first).

### Within Each User Story

- Models before services
- Services before endpoints/handlers
- Core implementation before integration
- Unit tests parallel with implementation where marked [P]
- Integration tests after all story components are built
- Story complete before moving to next priority (for sequential execution)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002–T008, T010–T013)
- All Foundational model tasks marked [P] can run in parallel (T015–T018)
- US4 (Priority/Tags/Search) can run in parallel with US1 after Foundational
- US2 and US3 can run in parallel after US1 completes
- US5 can run in parallel with US2/US3 after US1 completes
- All Dockerfiles (T072–T076) can run in parallel
- All Helm charts (T077–T081) can run in parallel
- CI and CD workflows (T084–T085) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch unit tests in parallel:
Task: "Unit tests for TaskService in services/backend/tests/unit/test_task_service.py"
Task: "Unit tests for EventPublisher in services/backend/tests/unit/test_event_publisher.py"
Task: "Unit tests for AuditLogService in services/audit/tests/unit/test_audit_service.py"
```

## Parallel Example: Dockerfiles (User Story 6)

```bash
# Launch all Dockerfiles in parallel:
Task: "Dockerfile for Backend in services/backend/Dockerfile"
Task: "Dockerfile for Notification in services/notification/Dockerfile"
Task: "Dockerfile for Recurring Task in services/recurring-task/Dockerfile"
Task: "Dockerfile for Audit in services/audit/Dockerfile"
Task: "Dockerfile for Frontend in services/frontend/Dockerfile"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Task Event Publishing + Audit)
4. **STOP and VALIDATE**: Test task CRUD + events + audit independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Task Events + Audit) → Test → MVP!
3. US2 (Recurring Tasks) → Test → Demo recurring flow
4. US3 (Reminders) → Test → Demo notification flow
5. US4 (Priority/Tags/Search) → Test → Demo organization features
6. US5 (Real-Time Sync) → Test → Demo multi-client updates
7. US6 (Minikube) → Test → Local deployment validated
8. US7 (Cloud + CI/CD) → Test → Production-grade deployment

### Parallel Team Strategy

With multiple developers after Foundational completes:

- Developer A: US1 (Task Events) → then US2 (Recurring) or US5 (Real-Time)
- Developer B: US4 (Priority/Tags/Search) — independent of US1
- Developer C: US3 (Reminders) — after US1 completes
- All: US6 + US7 after application stories complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- All services use Dapr abstractions — no direct Kafka/DB connections (Constitution Principle V)
- All code artifacts MUST include `[Task]: <ID>` referencing this tasks.md (Constitution Development Standards)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
