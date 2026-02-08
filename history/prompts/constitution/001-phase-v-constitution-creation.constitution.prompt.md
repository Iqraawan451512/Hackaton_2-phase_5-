---
id: 001
title: Phase V Constitution Creation
stage: constitution
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: user
command: /sp.constitution
labels: ["constitution", "governance", "phase-v", "microservices"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A
---

## Prompt

# speckit.constitution

## Purpose
This constitution defines the **principles, constraints, and standards** for Phase V of the Todo Chatbot project. All agents (Claude, Copilot, Gemini, etc.) MUST follow these rules strictly. No code or architecture changes are allowed outside these rules.

---

## Architecture Principles

1. **Spec-Driven Development (SDD) Only**
   - Every feature must be defined in `speckit.specify`, planned in `speckit.plan`, broken into tasks in `speckit.tasks` before any implementation.
   - No freestyle coding allowed.

2. **Microservices Architecture**
   - Frontend, Backend (Chat API + MCP), Notification, Recurring Task, Audit Service must be separate services/pods.
   - Communication via **Kafka** (or Dapr Pub/Sub abstraction) only.

3. **Event-Driven Design**
   - All task CRUD operations, reminders, recurring tasks must produce events to Kafka topics.
   - Agents must use Dapr Pub/Sub API wherever possible.

4. **Loose Coupling**
   - Services must not directly call each other's internal APIs.
   - All inter-service communication goes through Dapr sidecar or Kafka.

5. **Dapr Usage**
   - Mandatory for: Pub/Sub, State Management, Jobs (Scheduled Reminders), Secrets, Service Invocation.
   - No direct DB or Kafka connections in service code (except for testing).

6. **Database / State**
   - PostgreSQL/Neon DB for persistent state.
   - Use Dapr state store abstraction to access DB.
   - Conversation state and task cache stored in Dapr state.

7. **Secrets Management**
   - All API keys, DB credentials stored in Dapr Secrets or Kubernetes Secrets.
   - No hardcoded credentials.

8. **Containerization**
   - All services must be containerized using Docker.
   - Each service should have a minimal Dockerfile suitable for production.

9. **Kubernetes Deployment**
   - Services must be deployable to Minikube locally and GKE/AKS/OKE in cloud.
   - Use Helm charts wherever possible.
   - Dapr sidecar must run with every pod.

10. **Kafka Topics**
    - task-events → CRUD events for tasks
    - reminders → Due date notifications
    - task-updates → Real-time client sync
    - Agents cannot create additional topics without plan update.

11. **Logging & Monitoring**
    - Each service must emit structured logs.
    - Monitoring enabled via Kubernetes native tools or cloud equivalents.

12. **CI/CD**
    - Github Actions required for deployment.
    - Build, test, and deploy pipelines must be automated.

---

## Development Standards

1. **Code Style**
   - Python → PEP8
   - JS/TS → Prettier + ESLint
   - Comments required for every task-implemented block linking to `speckit.tasks`.

2. **Task Linking**
   - Every code artifact must include `[Task]: <ID>` referencing `speckit.tasks`.
   - No code without approved Task.

3. **Testing**
   - Unit tests required for every service function.
   - Integration tests for event-driven behavior.

4. **Security**
   - No secrets in environment variables.
   - HTTPS endpoints where applicable.
   - Validate all user inputs.

---

## Constraints

1. Only tools approved in Phase V: **Docker, Kubernetes, Minikube, AKS/GKE/OKE, Dapr, Kafka (Redpanda or Strimzi), Neon DB, Github Actions**.
2. No direct modifications to existing Phase IV backend/frontend structure unless approved in plan.
3. All new features must reference Task ID and Spec.
4. Max 1 replica of Kafka and Zookeeper for Minikube (local dev).
5. Production-grade cloud deployment must be highly available with at least 2 replicas of each pod.

---

## Failure Rules (What Agents Must NOT Do)

- Do not implement features without Spec + Task.
- Do not hardcode endpoints or credentials.
- Do not bypass Dapr sidecar or Kafka.
- Do not introduce unsupported technologies.
- Do not skip CI/CD or logging.

---

# End of Constitution

## Response snapshot

Created the Phase V Todo Chatbot Constitution (v1.0.0) at `.specify/memory/constitution.md`. Adapted the 6-principle template to accommodate the user's 12 architecture principles, 4 development standards, 5 constraints, and 5 failure rules. All placeholders replaced. Consistency propagation validated against plan-template.md, spec-template.md, and tasks-template.md — no updates required. Sync Impact Report embedded as HTML comment at top of constitution file. Version: 1.0.0, ratified 2026-02-08.

## Outcome

- ✅ Impact: Constitution created from scratch — all 12 architecture principles, development standards, constraints, failure rules, and governance encoded.
- 🧪 Tests: N/A (governance document, no code tests)
- 📁 Files: .specify/memory/constitution.md (created/overwritten)
- 🔁 Next prompts: /sp.specify for first feature spec, /sp.plan for architecture planning
- 🧠 Reflection: Template had 6 principle slots; user provided 12 principles plus additional sections. Extended template structure to fit all input. No information was lost.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual validation PASS — no unresolved placeholders, version line matches report, dates in ISO format, principles are declarative and testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
