# Implementation Plan: Advanced Cloud Deployment

**Branch**: `001-advanced-cloud-deployment` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-advanced-cloud-deployment/spec.md`

## Summary

Phase V extends the existing Todo Chatbot with event-driven
architecture, advanced task features (recurring tasks, due dates,
reminders, priority, tags, search/filter/sort), real-time client
sync, and production-grade deployment to Kubernetes. The
architecture uses 5 microservices communicating exclusively
through Dapr Pub/Sub over Kafka, with Dapr providing state
management, job scheduling, secrets, and service invocation.
Deployment targets both Minikube (local) and GKE/AKS/OKE (cloud)
with CI/CD via GitHub Actions.

## Technical Context

**Language/Version**: Python 3.11 (Backend, Notification,
Recurring Task, Audit services), TypeScript/Node 20 (Frontend)
**Primary Dependencies**: FastAPI 0.110+, MCP SDK, Dapr SDK
for Python 1.13+, Next.js 14+, Dapr JS SDK, confluent-kafka
(testing only), Helm 3.14+
**Storage**: PostgreSQL 16 (Neon DB) via Dapr state store
abstraction; Kafka (Redpanda or Strimzi) for event streaming
**Testing**: pytest (Python services), Jest + React Testing
Library (Frontend), integration tests via Dapr test containers
**Target Platform**: Kubernetes (Minikube local, GKE/AKS/OKE
cloud), Docker containers, Linux-based pods
**Project Type**: Web application (microservices)
**Performance Goals**: Event publishing <1s latency, real-time
sync <2s, reminder delivery <60s of scheduled time
**Constraints**: Max 1 Kafka/Zookeeper replica on Minikube;
min 2 replicas per pod in cloud; no direct DB/Kafka calls in
service code
**Scale/Scope**: 5 microservices, 3 Kafka topics, 4 Dapr
components, 2 deployment targets (local + cloud)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after
Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | SDD Only | PASS | Spec and plan created before implementation |
| II | Microservices Architecture | PASS | 5 separate services: Frontend, Backend, Notification, Recurring Task, Audit |
| III | Event-Driven Design | PASS | All CRUD → `task-events`, reminders → `reminders`, sync → `task-updates` |
| IV | Loose Coupling | PASS | All inter-service via Dapr sidecar/Kafka; no direct API calls |
| V | Dapr Usage | PASS | Pub/Sub, State, Jobs, Secrets, Service Invocation all via Dapr |
| VI | Database/State | PASS | Neon DB via Dapr state store; conversation state in Dapr |
| VII | Secrets Management | PASS | Dapr Secrets + Kubernetes Secrets; no hardcoded credentials |
| VIII | Containerization | PASS | Docker containers for all 5 services |
| IX | Kubernetes Deployment | PASS | Minikube + cloud K8s; Helm charts; Dapr sidecar on every pod |
| X | Kafka Topics | PASS | Only approved topics: task-events, reminders, task-updates |
| XI | Logging & Monitoring | PASS | Structured logging in all services; K8s monitoring |
| XII | CI/CD | PASS | GitHub Actions for build, test, deploy |

**Gate Result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-advanced-cloud-deployment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── backend-api.yaml # OpenAPI spec for Backend Service
│   ├── task-events.json # Event schema for task-events topic
│   ├── reminders.json   # Event schema for reminders topic
│   └── task-updates.json# Event schema for task-updates topic
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
services/
├── backend/
│   ├── src/
│   │   ├── models/          # Task, Reminder, Tag data models
│   │   ├── services/        # Task service, event publisher, reminder scheduler
│   │   ├── api/             # FastAPI routes (/api/tasks, /api/jobs)
│   │   ├── events/          # Event schemas and Dapr Pub/Sub handlers
│   │   └── config.py        # Dapr client config, logging setup
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── Dockerfile
│   └── requirements.txt
│
├── notification/
│   ├── src/
│   │   ├── handlers/        # Kafka/Dapr subscription handlers
│   │   ├── services/        # Notification delivery (push/email)
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── recurring-task/
│   ├── src/
│   │   ├── handlers/        # task-events subscription handler
│   │   ├── services/        # Recurring task creation logic
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── audit/
│   ├── src/
│   │   ├── handlers/        # task-events subscription handler
│   │   ├── services/        # Audit log persistence
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/      # Task list, task form, filters, search
    │   ├── pages/           # Next.js pages
    │   ├── services/        # API client, WebSocket client
    │   └── hooks/           # React hooks for real-time updates
    ├── tests/
    ├── Dockerfile
    └── package.json

deploy/
├── helm/
│   ├── backend/
│   ├── notification/
│   ├── recurring-task/
│   ├── audit/
│   ├── frontend/
│   └── kafka/               # Redpanda/Strimzi Helm values
├── dapr/
│   ├── pubsub.yaml          # kafka-pubsub component
│   ├── statestore.yaml      # state.postgresql component
│   ├── secrets.yaml          # secretstores.kubernetes component
│   └── jobs.yaml             # jobs component
├── minikube/
│   └── deploy.sh            # Local deployment script
└── cloud/
    └── deploy.sh            # Cloud deployment script

.github/
└── workflows/
    ├── ci.yaml              # Build + test on PR
    └── cd.yaml              # Deploy to cloud on merge to main
```

**Structure Decision**: Microservices layout with each service in
`services/<name>/` and shared deployment config in `deploy/`.
This maps directly to the constitution's requirement for separate
services/pods (Principle II) and Helm-based Kubernetes deployment
(Principle IX).

## Architecture Overview

### High-Level Components

1. **Backend Service** (FastAPI + MCP)
   - Task CRUD via REST API
   - Event publishing to `task-events` and `task-updates` via
     Dapr Pub/Sub
   - Reminder scheduling via Dapr Jobs API
   - State management via Dapr state store
   - Secrets via Dapr Secrets API

2. **Frontend Service** (Next.js)
   - User interface for task management
   - Search, filter, sort controls
   - WebSocket client for real-time updates
   - Communicates with Backend via Dapr Service Invocation

3. **Notification Service** (FastAPI)
   - Subscribes to `reminders` topic via Dapr Pub/Sub
   - Delivers push notifications to users
   - Structured logging for delivery tracking

4. **Recurring Task Service** (FastAPI)
   - Subscribes to `task-events` topic via Dapr Pub/Sub
   - Listens for `task.completed` events on recurring tasks
   - Creates next task instance via Backend API (Dapr Service
     Invocation)

5. **Audit Service** (FastAPI)
   - Subscribes to `task-events` topic via Dapr Pub/Sub
   - Persists all events as audit log entries
   - Provides audit trail query capabilities

6. **Infrastructure**
   - Kafka (Redpanda/Strimzi): 3 topics
   - PostgreSQL (Neon DB): persistent storage
   - Dapr: sidecar on every pod
   - Kubernetes: orchestration (Minikube + cloud)

### Component Interaction Flows

**Task CRUD Flow**:
```
Frontend → Dapr Service Invocation → Backend Service
  → Dapr State Store (persist to Neon DB)
  → Dapr Pub/Sub → task-events topic
    → Audit Service (stores event)
    → Recurring Task Service (checks recurrence)
  → Dapr Pub/Sub → task-updates topic
    → Frontend WebSocket (real-time update)
```

**Recurring Task Flow**:
```
Recurring Task Service ← task-events (task.completed)
  → Check if task has recurrence pattern
  → If yes: Dapr Service Invocation → Backend Service
    → Create next task instance (new due date)
    → Publishes task.created → task-events
```

**Reminder Notification Flow**:
```
Backend Service → Dapr Jobs API (schedule reminder)
  → At due time: Dapr triggers callback
  → Backend → Dapr Pub/Sub → reminders topic
    → Notification Service (delivers to user)
```

**Real-Time Client Sync**:
```
Backend → Dapr Pub/Sub → task-updates topic
  → WebSocket relay → All connected clients
```

### Dapr Components

| Component | Type | Backend | Details |
|-----------|------|---------|---------|
| kafka-pubsub | pubsub.kafka | Redpanda/Strimzi | Topics: task-events, reminders, task-updates |
| statestore | state.postgresql | Neon DB | Task state, conversation cache |
| dapr-jobs | jobs | Dapr scheduler | Reminder scheduling |
| kubernetes-secrets | secretstores.kubernetes | K8s Secrets | API keys, DB credentials |

### Kubernetes Deployment

**Minikube (Local)**:
- 5 service pods + Dapr sidecars (auto-injected)
- 1 Kafka replica + 1 Zookeeper replica (constitution limit)
- Dapr components deployed as K8s CRDs
- Helm charts for each service

**Cloud (GKE/AKS/OKE)**:
- Same 5 service pods, min 2 replicas each
- Managed or self-hosted Kafka (Redpanda Cloud / Strimzi)
- GitHub Actions CI/CD: build → test → deploy
- Dapr observability + K8s native monitoring

### API Endpoints

| Endpoint | Method | Service | Purpose |
|----------|--------|---------|---------|
| /api/tasks | GET | Backend | List tasks (with search, filter, sort params) |
| /api/tasks | POST | Backend | Create task (with optional recurrence, due date, priority, tags) |
| /api/tasks/{id} | GET | Backend | Get single task |
| /api/tasks/{id} | PATCH | Backend | Update task fields |
| /api/tasks/{id} | DELETE | Backend | Delete task |
| /api/tasks/{id}/complete | POST | Backend | Mark task complete (triggers recurrence) |
| /api/tasks/{id}/tags | PUT | Backend | Update task tags |
| /dapr/subscribe | GET | All consumers | Dapr subscription endpoint (auto-configured) |
| /events/task-events | POST | Audit, Recurring | Dapr Pub/Sub delivery endpoint |
| /events/reminders | POST | Notification | Dapr Pub/Sub delivery endpoint |
| /events/task-updates | POST | Frontend relay | Dapr Pub/Sub delivery endpoint |
| /api/jobs/trigger | POST | Backend | Dapr Jobs callback for scheduled reminders |

### Sequencing & Deployment Order

1. **Infrastructure First**:
   - Deploy Kafka (Redpanda / Strimzi)
   - Apply Dapr component CRDs (pubsub, statestore, secrets, jobs)
   - Verify Neon DB connectivity

2. **Core Services**:
   - Deploy Backend Service with Dapr sidecar
   - Verify task CRUD + event publishing

3. **Consumer Services** (can deploy in parallel):
   - Deploy Audit Service → verify event consumption
   - Deploy Recurring Task Service → verify recurrence logic
   - Deploy Notification Service → verify reminder delivery

4. **Frontend**:
   - Deploy Frontend Service with Dapr sidecar
   - Verify end-to-end flow + WebSocket real-time sync

5. **CI/CD**:
   - Configure GitHub Actions workflows
   - Validate pipeline: build → test → deploy

## Complexity Tracking

> No constitution violations detected — this section is empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
