<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 (template) → 1.0.0
  Modified principles: N/A (initial creation from template)
  Added sections:
    - Core Principles (12 architecture principles)
    - Development Standards (code style, task linking, testing, security)
    - Constraints (technology and deployment constraints)
    - Failure Rules (agent guardrails)
    - Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no update needed
      (Constitution Check section is dynamically filled at plan time)
    - .specify/templates/spec-template.md ✅ no update needed
      (spec template is requirement-focused, not constitution-coupled)
    - .specify/templates/tasks-template.md ✅ no update needed
      (task phases and structure are compatible with constitution)
  Follow-up TODOs: None
-->

# Todo Chatbot Phase V Constitution

## Core Principles

### I. Spec-Driven Development (SDD) Only

- Every feature MUST be defined in `speckit.specify`, planned in
  `speckit.plan`, and broken into tasks in `speckit.tasks` before
  any implementation begins.
- No freestyle coding is allowed.
- Rationale: Enforces traceability, prevents scope creep, and
  ensures all work is reviewable against a specification.

### II. Microservices Architecture

- The system MUST be composed of separate services/pods:
  Frontend, Backend (Chat API + MCP), Notification Service,
  Recurring Task Service, and Audit Service.
- Communication between services MUST use Kafka (or Dapr
  Pub/Sub abstraction) only.
- Rationale: Enables independent deployment, scaling, and
  fault isolation for each service.

### III. Event-Driven Design

- All task CRUD operations, reminders, and recurring task
  triggers MUST produce events to Kafka topics.
- Agents MUST use the Dapr Pub/Sub API wherever possible.
- Rationale: Decouples producers from consumers and enables
  asynchronous, resilient processing.

### IV. Loose Coupling

- Services MUST NOT directly call each other's internal APIs.
- All inter-service communication MUST go through the Dapr
  sidecar or Kafka.
- Rationale: Prevents tight coupling, allows independent
  evolution of each service.

### V. Dapr Usage

- Dapr is MANDATORY for: Pub/Sub, State Management,
  Jobs (Scheduled Reminders), Secrets, and Service Invocation.
- No direct DB or Kafka connections in service code
  (except for testing).
- Rationale: Provides a portable, consistent abstraction layer
  that simplifies cloud-native development.

### VI. Database / State

- PostgreSQL (Neon DB) MUST be used for persistent state.
- All data access MUST use the Dapr state store abstraction.
- Conversation state and task cache MUST be stored in Dapr state.
- Rationale: Ensures portability across environments and
  consistent state management patterns.

### VII. Secrets Management

- All API keys and DB credentials MUST be stored in Dapr Secrets
  or Kubernetes Secrets.
- No hardcoded credentials are permitted anywhere in the codebase.
- Rationale: Prevents credential leakage and supports rotation
  without code changes.

### VIII. Containerization

- All services MUST be containerized using Docker.
- Each service MUST have a minimal Dockerfile suitable for
  production deployment.
- Rationale: Ensures reproducible builds and consistent
  runtime environments.

### IX. Kubernetes Deployment

- Services MUST be deployable to Minikube locally and
  GKE/AKS/OKE in cloud.
- Helm charts MUST be used wherever possible.
- The Dapr sidecar MUST run with every pod.
- Rationale: Provides a consistent orchestration layer across
  local development and production environments.

### X. Kafka Topics

- Approved topics:
  - `task-events` — CRUD events for tasks
  - `reminders` — Due date notifications
  - `task-updates` — Real-time client sync
- Agents MUST NOT create additional topics without an approved
  plan update.
- Rationale: Controls event topology, prevents topic sprawl,
  and keeps the event schema manageable.

### XI. Logging & Monitoring

- Each service MUST emit structured logs.
- Monitoring MUST be enabled via Kubernetes native tools or
  cloud equivalents.
- Rationale: Enables observability, debugging, and alerting
  across all services.

### XII. CI/CD

- GitHub Actions is REQUIRED for all deployment pipelines.
- Build, test, and deploy pipelines MUST be fully automated.
- Rationale: Ensures consistent, repeatable, and auditable
  delivery of changes.

## Development Standards

### Code Style

- Python code MUST follow PEP 8.
- JavaScript/TypeScript code MUST use Prettier + ESLint.
- Comments MUST be included for every task-implemented block,
  linking to the corresponding `speckit.tasks` task ID.

### Task Linking

- Every code artifact MUST include `[Task]: <ID>` referencing
  a task in `speckit.tasks`.
- No code MUST be committed without an approved Task.

### Testing

- Unit tests are REQUIRED for every service function.
- Integration tests are REQUIRED for event-driven behavior
  (Kafka/Dapr Pub/Sub flows).

### Security

- No secrets in environment variables or source code.
- HTTPS endpoints MUST be used where applicable.
- All user inputs MUST be validated.

## Constraints

1. Only tools approved for Phase V are permitted: **Docker,
   Kubernetes, Minikube, AKS/GKE/OKE, Dapr, Kafka (Redpanda
   or Strimzi), Neon DB, GitHub Actions**.
2. No direct modifications to existing Phase IV
   backend/frontend structure unless approved in plan.
3. All new features MUST reference a Task ID and Spec.
4. Max 1 replica of Kafka and Zookeeper for Minikube
   (local development).
5. Production-grade cloud deployment MUST be highly available
   with at least 2 replicas of each pod.

## Failure Rules

Agents MUST NOT:

- Implement features without an approved Spec + Task.
- Hardcode endpoints or credentials.
- Bypass the Dapr sidecar or Kafka for inter-service
  communication.
- Introduce technologies not listed in the approved tool set.
- Skip CI/CD pipelines or structured logging.

## Governance

- This constitution supersedes all other development practices
  for Phase V of the Todo Chatbot project.
- All PRs and code reviews MUST verify compliance with these
  principles and constraints.
- Amendments to this constitution REQUIRE:
  1. A documented proposal describing the change and rationale.
  2. Approval from the project architect.
  3. A migration plan if the change affects existing artifacts.
- Complexity beyond these principles MUST be justified via an
  Architecture Decision Record (ADR).
- Version increments follow semantic versioning:
  - MAJOR: Backward-incompatible governance or principle changes.
  - MINOR: New principles, sections, or material expansions.
  - PATCH: Clarifications, wording, or typo fixes.
- Runtime development guidance is available in `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-02-08 | **Last Amended**: 2026-02-08
