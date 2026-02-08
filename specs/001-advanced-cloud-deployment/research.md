# Research: Advanced Cloud Deployment

**Branch**: `001-advanced-cloud-deployment`
**Date**: 2026-02-08
**Status**: Complete

## Research Areas

### R1: Dapr Pub/Sub with Kafka

**Decision**: Use Dapr Pub/Sub component (`pubsub.kafka`) with
Redpanda as the Kafka-compatible broker for local development,
Strimzi operator for cloud.

**Rationale**: Dapr abstracts the Kafka client, so service code
uses the Dapr HTTP/gRPC API instead of direct Kafka connections.
Redpanda is lightweight and Kafka-compatible, ideal for
single-replica Minikube. Strimzi provides operator-managed Kafka
on production Kubernetes.

**Alternatives considered**:
- Direct confluent-kafka Python client: Rejected — violates
  Constitution Principle V (Dapr mandatory).
- RabbitMQ via Dapr: Rejected — constitution specifies Kafka.
- Apache Kafka (vanilla): Heavier than Redpanda for local dev;
  Redpanda is wire-compatible and lighter.

### R2: Dapr State Store for PostgreSQL

**Decision**: Use Dapr state store component (`state.postgresql`)
backed by Neon DB.

**Rationale**: Dapr state store provides key-value semantics over
PostgreSQL. For task CRUD, the Backend Service stores task
objects as JSON values keyed by task ID. This satisfies
Constitution Principle VI without direct DB connections.

**Alternatives considered**:
- SQLAlchemy ORM directly: Rejected — violates Principle V/VI
  (must use Dapr abstraction).
- Redis state store: Rejected — constitution mandates PostgreSQL
  for persistent state.
- Dapr state store with etag concurrency: Adopted for
  last-write-wins conflict resolution.

### R3: Dapr Jobs API for Scheduled Reminders

**Decision**: Use Dapr Jobs API to schedule reminder callbacks
at task due dates minus 30 minutes (default lead time).

**Rationale**: Dapr Jobs provides at-least-once scheduling
without external cron or scheduler services. The Backend
Service schedules a job when a due date is set; the job calls
back to `/api/jobs/trigger` on the Backend, which then publishes
to the `reminders` topic.

**Alternatives considered**:
- Kubernetes CronJobs: Rejected — per-task CronJobs don't scale
  and aren't dynamic.
- APScheduler in-process: Rejected — not distributed, lost on
  pod restart.
- Celery + Redis Beat: Rejected — introduces unapproved
  technology (Redis for task queue).

### R4: Real-Time Client Sync via WebSocket

**Decision**: Backend consumes `task-updates` topic via Dapr
subscription and relays events to connected WebSocket clients.

**Rationale**: The Backend (or a lightweight relay within it)
subscribes to `task-updates` via Dapr Pub/Sub. When an event
arrives, it broadcasts to all WebSocket-connected clients.
This keeps the architecture simple — no separate WebSocket
service pod needed. The Backend already runs with a Dapr
sidecar.

**Alternatives considered**:
- Server-Sent Events (SSE): Simpler but one-directional; less
  flexible for future bidirectional needs.
- Separate WebSocket microservice: Adds a 6th service;
  unnecessary complexity for the current scope.
- Polling: Rejected — does not meet the <2s real-time
  requirement.

### R5: Kafka Broker Choice (Redpanda vs Strimzi)

**Decision**: Redpanda for Minikube (lightweight, single-node),
Strimzi operator for cloud (production-grade, managed).

**Rationale**: Redpanda runs without Zookeeper and uses less
memory (satisfies the 1-replica Minikube constraint). Strimzi
provides operator-managed Kafka on Kubernetes with automated
topic management, replication, and monitoring.

**Alternatives considered**:
- Confluent Cloud: Managed but adds cost and external
  dependency; Strimzi is self-hosted.
- Amazon MSK: Cloud-specific; not portable across GKE/AKS/OKE.

### R6: Frontend Framework (Next.js)

**Decision**: Next.js 14+ with TypeScript for the Frontend
Service.

**Rationale**: User-specified in the plan input. Next.js
provides SSR/SSG, API routes (for WebSocket upgrade), and
strong TypeScript support. The existing Phase IV frontend can
be migrated or extended.

**Alternatives considered**:
- Vite + React SPA: Lighter but lacks SSR; Next.js aligns with
  the user's specification.
- Angular: Not specified by user; team familiarity assumed with
  Next.js.

### R7: CI/CD Pipeline Design

**Decision**: Two GitHub Actions workflows — `ci.yaml` (on PR)
and `cd.yaml` (on merge to main).

**Rationale**: CI builds and tests all services on every PR.
CD deploys to the cloud cluster on merge to main. Each service
has its own Docker build step. Helm upgrade commands deploy
updated images.

**Alternatives considered**:
- Single monolithic workflow: Harder to debug; slower feedback.
- ArgoCD/FluxCD GitOps: More complex; GitHub Actions satisfies
  constitution requirement (Principle XII).

## Unresolved Items

None. All technical decisions resolved.
