# Quickstart: Advanced Cloud Deployment

**Branch**: `001-advanced-cloud-deployment`
**Date**: 2026-02-08

## Prerequisites

- Docker Desktop installed and running
- Minikube v1.32+ installed
- kubectl configured
- Helm 3.14+ installed
- Dapr CLI v1.13+ installed
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend services)
- Git

## Local Development Setup (Minikube)

### 1. Start Minikube

```bash
minikube start --cpus=4 --memory=8192
```

### 2. Install Dapr on Kubernetes

```bash
dapr init -k --wait
```

### 3. Deploy Kafka (Redpanda)

```bash
helm repo add redpanda https://charts.redpanda.com
helm install redpanda redpanda/redpanda \
  --set statefulset.replicas=1 \
  --set resources.cpu.cores=1 \
  --set resources.memory.container.max=1Gi \
  --namespace kafka --create-namespace
```

### 4. Apply Dapr Components

```bash
kubectl apply -f deploy/dapr/pubsub.yaml
kubectl apply -f deploy/dapr/statestore.yaml
kubectl apply -f deploy/dapr/secrets.yaml
kubectl apply -f deploy/dapr/jobs.yaml
```

### 5. Deploy Services

**Option A — Automated (recommended):**

```bash
bash deploy/minikube/deploy.sh
```

**Option B — Manual:**

```bash
# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build all service images
docker build -t todo-chatbot/backend:latest services/backend/
docker build -t todo-chatbot/notification:latest services/notification/
docker build -t todo-chatbot/recurring-task:latest services/recurring-task/
docker build -t todo-chatbot/audit:latest services/audit/
docker build -t todo-chatbot/frontend:latest services/frontend/

# Deploy via Helm
helm install backend deploy/helm/backend/ -n todo-chatbot --create-namespace
helm install notification deploy/helm/notification/ -n todo-chatbot
helm install recurring-task deploy/helm/recurring-task/ -n todo-chatbot
helm install audit deploy/helm/audit/ -n todo-chatbot
helm install frontend deploy/helm/frontend/ -n todo-chatbot
```

### 6. Verify Deployment

```bash
# Check all pods are running with Dapr sidecars
kubectl get pods -n todo-chatbot

# Expected output: each service pod shows 2/2 containers
# (1 app + 1 daprd sidecar)

# Run the automated smoke test
bash deploy/minikube/smoke-test.sh

# Or manually port-forward and access:
kubectl port-forward -n todo-chatbot svc/frontend-frontend 3000:3000

# Access the app at http://localhost:3000
```

## Smoke Test

1. Open http://localhost:3000
2. Create a task with title "Test Task", priority "High",
   tag "test", due date tomorrow
3. Verify the task appears in the task list
4. Open a second browser tab to the same URL
5. Update the task in tab 1 — verify it updates in tab 2
   within 2 seconds
6. Mark the task complete — verify audit log captures the event
7. Create a recurring daily task — mark it complete — verify
   next instance is auto-created

## Cloud Deployment

Cloud deployment is automated via GitHub Actions. See
`.github/workflows/cd.yaml` for the full pipeline.

Manual cloud deployment:

```bash
# Authenticate to your cloud K8s cluster
# (GKE, AKS, or OKE — see provider docs)

# Run the cloud deploy script
bash deploy/cloud/deploy.sh
```

## Troubleshooting

- **Dapr sidecar not injecting**: Ensure the namespace has the
  `dapr.io/enabled: "true"` annotation.
- **Kafka connection errors**: Verify Redpanda is running with
  `kubectl get pods -n kafka`.
- **State store errors**: Check Neon DB connection string in
  Kubernetes secrets.
- **WebSocket not connecting**: Verify the frontend service
  is port-forwarded and the Backend's WebSocket endpoint is
  accessible.
