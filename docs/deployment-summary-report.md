# Todo Chatbot — Production Deployment Summary Report

**Project:** Todo Chatbot (Phase V — Advanced Cloud Deployment)
**Repository:** https://github.com/Iqraawan451512/Hackaton_2-phase_5-
**Date:** 2026-02-09
**Architecture:** Event-driven microservices on Kubernetes with Dapr middleware

---

## 1. CI/CD Pipeline

The project uses **GitHub Actions** for fully automated continuous integration and deployment.

### CI Pipeline (`.github/workflows/ci.yaml`)
- **Trigger:** Pull requests to `master`
- **Jobs (parallel):**
  - Unit tests for all 4 Python services (pytest)
  - Frontend tests (Jest) and linting (ESLint)
  - Python linting (ruff) across all backend services
  - Docker build verification for all 5 images
- **Purpose:** Ensures code quality before merging

### CD Pipeline (`.github/workflows/deploy.yml`)
- **Trigger:** Push to `master` (after PR merge)
- **Stage 1 — Build & Push (parallel):**
  - Builds Docker images for 5 services using Docker Buildx
  - Pushes to GitHub Container Registry (GHCR) with SHA + `latest` tags
  - Uses GitHub Actions cache for faster builds
- **Stage 2 — Deploy (sequential):**
  - Configures kubectl using `KUBE_CONFIG` secret
  - Applies Dapr component manifests (Pub/Sub, State Store, Secrets, Jobs)
  - Deploys each service via Helm with `--atomic` (auto-rollback on failure)
  - Verifies all pods are running and services have endpoints
- **Security:** Minimal permissions (`contents: read`, `packages: write`), production environment with optional approval gates

**Flow:** `git push` → Build 5 images → Push to GHCR → Helm deploy → Verify

---

## 2. Kubernetes Cluster Setup

### Cluster Specifications
| Component | Configuration |
|-----------|--------------|
| **Provider** | GKE / AKS / OKE (cloud-agnostic) |
| **Namespace** | `todo-chatbot` |
| **Services** | 5 microservices (10 pods total) |
| **Middleware** | Dapr sidecar injection (2 containers per pod) |
| **Message Broker** | Redpanda (Kafka-compatible, 2+ replicas) |

### Service Architecture
```
Internet → LoadBalancer → Frontend (Next.js, port 3000)
                              ↓
                         Backend (FastAPI, port 8000) ← ClusterIP
                          ↙     ↓       ↘
              Notification  Recurring   Audit        ← ClusterIP
              (port 8001)   (port 8002) (port 8003)
                          ↕
                    Redpanda (Kafka)
                    3 topics: task-events, reminders, task-updates
```

### Service Exposure
| Service | Type | Access | Replicas |
|---------|------|--------|----------|
| Frontend | LoadBalancer | Public (external IP) | 2 |
| Backend | ClusterIP | Internal only | 2 |
| Notification | ClusterIP | Internal only | 2 |
| Recurring Task | ClusterIP | Internal only | 2 |
| Audit | ClusterIP | Internal only | 2 |

---

## 3. Helm Deployment

All services are deployed using **Helm v3** charts located in `deploy/helm/`.

### Chart Structure (per service)
```
deploy/helm/<service>/
├── Chart.yaml                  # Chart metadata
├── values.yaml                 # Default (Minikube) values
├── values-cloud.yaml           # Cloud values (2 replicas)
├── values-production.yaml      # Production values (full config)
└── templates/
    ├── deployment.yaml         # K8s Deployment with Dapr annotations
    └── service.yaml            # K8s Service (ClusterIP/LoadBalancer)
```

### Production Values Highlights
- **2 replicas** per service for high availability
- **Resource limits:** 200m-1000m CPU, 256Mi-512Mi memory per pod
- **Image pull policy:** `Always` (ensures deployed tag is current)
- **Dapr sidecar injection** via pod annotations
- **Health checks:** Liveness probe (10s delay, 15s interval) + readiness probe (5s delay, 10s interval)
- **Atomic deploys:** `--atomic` flag ensures automatic rollback on failure

### Deployment Command (per service)
```bash
helm upgrade --install <service> deploy/helm/<service> \
  -n todo-chatbot \
  -f deploy/helm/<service>/values-production.yaml \
  --set image.repository=ghcr.io/<owner>/todo-chatbot/<service> \
  --set image.tag=<commit-sha> \
  --wait --timeout 5m --atomic
```

---

## 4. Secrets Management

### Strategy: Kubernetes Secrets + Dapr Secret Store

| Layer | Mechanism | What It Stores |
|-------|-----------|----------------|
| **GitHub Actions** | Repository Secrets | `KUBE_CONFIG` (cluster access), `GITHUB_TOKEN` (GHCR push) |
| **Kubernetes** | K8s Secrets | API keys, database credentials, service tokens |
| **Dapr** | Secret Store component (`secrets.yaml`) | Abstracts K8s secrets for application access |

### Security Practices
- No secrets hardcoded in code, Dockerfiles, or Helm values
- `KUBE_CONFIG` stored as encrypted GitHub secret — never exposed in logs
- `GITHUB_TOKEN` is ephemeral (auto-generated per workflow run)
- Dapr Secret Store component provides a uniform API for all services to retrieve secrets without direct K8s API access
- Production environment in GitHub can require manual approval before deploy

---

## 5. Production Environment

### GitHub Environment: `production`
- **Purpose:** Gates deployment with optional review/approval
- **Configuration:**
  - Required reviewers (optional but recommended)
  - Deployment branch restriction: `master` only
  - Environment secrets: `KUBE_CONFIG`
- **Benefit:** Prevents accidental deployments; creates audit trail of who approved each release

### Production Safeguards
| Safeguard | Implementation |
|-----------|---------------|
| Atomic deploys | `--atomic` flag — auto-rollback on Helm failure |
| Concurrency control | Only one deploy runs at a time (no overlapping) |
| Health checks | Liveness + readiness probes on every service |
| Image tagging | Git SHA tags — every deployment is traceable to a commit |
| Namespace isolation | All resources in `todo-chatbot` namespace |

---

## 6. AI-Assisted Operations (kubectl-ai / Kagent)

### kubectl-ai — Human-in-the-Loop AI
An AI-powered kubectl plugin that converts natural language to kubectl commands.

**Key capabilities:**
- **Monitor:** `kubectl ai "show health of all pods in todo-chatbot"`
- **Troubleshoot:** `kubectl ai "why is the backend pod crashing?"`
- **Scale:** `kubectl ai "scale frontend to 4 replicas"`
- **Optimize:** `kubectl ai "which services are over-provisioned?"`
- **Rollback:** `kubectl ai "rollback backend to previous version"`

### Kagent — Autonomous AI Agent
A Kubernetes-native AI controller that runs inside the cluster for autonomous operations.

**Key capabilities:**
- **Auto-monitoring:** Watches pods every 5 minutes for crashes, OOMs, image pull errors
- **Auto-scaling:** Scales services based on CPU, memory, and latency thresholds
- **Auto-diagnostics:** Collects logs, describes resources, and analyzes events on failure
- **Auto-remediation:** Restarts crashed pods, increases memory for OOM-killed containers
- **Resource optimization:** Weekly reports on right-sizing based on actual usage patterns

### Combined AI Operations Model
```
kubectl-ai (on-demand)  +  Kagent (autonomous)
         ↓                        ↓
  Human asks questions     Agent watches 24/7
  Gets instant answers     Detects & fixes issues
  Manual interventions     Generates weekly reports
```

---

## 7. Why This Deployment Is Secure, Scalable, and Fully Automated

### Secure
- **Zero hardcoded secrets** — all credentials managed via GitHub Secrets + K8s Secrets + Dapr Secret Store
- **Minimal permissions** — GitHub Actions uses least-privilege (`contents: read`, `packages: write`)
- **Environment gating** — production deploys require explicit approval
- **Internal services isolated** — only frontend is publicly exposed via LoadBalancer
- **Image provenance** — every image tagged with git SHA for full traceability

### Scalable
- **2 replicas per service** — immediate high availability with zero single points of failure
- **Horizontal Pod Autoscaling** — can scale from 2 to 8+ replicas based on load
- **Event-driven architecture** — Kafka decouples services, enabling independent scaling
- **Resource budgets** — CPU/memory requests guarantee scheduling; limits prevent noisy neighbors
- **Cloud-agnostic** — deploys to GKE, AKS, or OKE without changes

### Fully Automated
- **Push-to-deploy** — `git push` to master triggers the entire pipeline
- **Parallel builds** — 5 Docker images built simultaneously
- **Atomic deploys** — failed deployments automatically roll back
- **Health verification** — post-deploy checks confirm all pods are running
- **AI-assisted operations** — kubectl-ai and Kagent reduce manual ops to near-zero

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                       │
│  PR → CI (test/lint/build) → Merge → CD (build/push/deploy) │
└──────────────────────┬──────────────────────────────────────┘
                       │ Docker images
                       ▼
              ┌─────────────────┐
              │  GitHub Container│
              │  Registry (GHCR) │
              └────────┬────────┘
                       │ helm upgrade --install
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster (GKE/AKS/OKE)            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Namespace: todo-chatbot                   │ │
│  │                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │ │
│  │  │ Frontend │  │ Backend  │  │  Audit   │  (x2 each)  │ │
│  │  │ :3000 LB │  │ :8000    │  │  :8003   │             │ │
│  │  └────┬─────┘  └────┬─────┘  └──────────┘             │ │
│  │       │              │                                  │ │
│  │  ┌────┴──────────────┴──────────────────┐              │ │
│  │  │         Dapr Sidecar Mesh            │              │ │
│  │  │  Pub/Sub │ State Store │ Secrets     │              │ │
│  │  └────┬──────────────┬──────────────────┘              │ │
│  │       │              │                                  │ │
│  │  ┌────┴─────┐  ┌─────┴────────┐                       │ │
│  │  │Notifier  │  │Recurring-Task│  (x2 each)            │ │
│  │  │ :8001    │  │  :8002       │                        │ │
│  │  └──────────┘  └──────────────┘                        │ │
│  │                                                         │ │
│  │  ┌──────────────────────────┐                          │ │
│  │  │  Redpanda (Kafka)        │  3 topics                │ │
│  │  │  task-events, reminders  │                          │ │
│  │  │  task-updates            │                          │ │
│  │  └──────────────────────────┘                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────┐  ┌───────────────────┐                  │
│  │  kubectl-ai    │  │  Kagent Agent     │  AI Operations   │
│  │  (on-demand)   │  │  (autonomous)     │                  │
│  └────────────────┘  └───────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
```

---

**Total Services:** 5 | **Total Pods:** 10 (2 replicas each) | **Kafka Topics:** 3
**CI Jobs:** 7 parallel | **CD Stages:** 2 (build → deploy) | **Deploy Time:** ~5 min
