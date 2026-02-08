#!/usr/bin/env bash
# [Task]: T082 — Minikube deployment script
# Deploys the complete Todo Chatbot stack to a local Minikube cluster.
#
# Prerequisites:
#   - minikube, kubectl, helm, dapr CLI installed
#   - Docker daemon running
#
# Usage: ./deploy/minikube/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NAMESPACE="todo-chatbot"

echo "=== Todo Chatbot Minikube Deployment ==="

# ── Step 1: Start Minikube ─────────────────────────────────
echo "[1/8] Starting Minikube cluster..."
if ! minikube status &>/dev/null; then
    minikube start --cpus=4 --memory=4096
else
    echo "  Minikube already running."
fi

# ── Step 2: Create namespace ───────────────────────────────
echo "[2/8] Creating namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# ── Step 3: Initialize Dapr ───────────────────────────────
echo "[3/8] Installing Dapr on the cluster..."
if ! dapr status -k &>/dev/null; then
    dapr init -k --wait
else
    echo "  Dapr already installed."
fi

# ── Step 4: Deploy Kafka (Redpanda) ──────────────────────
echo "[4/8] Deploying Kafka (Redpanda)..."
helm repo add redpanda https://charts.redpanda.com 2>/dev/null || true
helm repo update
helm upgrade --install redpanda redpanda/redpanda \
    -n "$NAMESPACE" \
    -f "$PROJECT_ROOT/deploy/helm/kafka/values.yaml" \
    --wait --timeout 5m

# ── Step 5: Apply Dapr components ─────────────────────────
echo "[5/8] Applying Dapr components..."
kubectl apply -f "$PROJECT_ROOT/deploy/dapr/" -n "$NAMESPACE"

# ── Step 6: Build Docker images ──────────────────────────
echo "[6/8] Building Docker images in Minikube's Docker context..."
eval "$(minikube docker-env)"

docker build -t todo-chatbot/backend:latest "$PROJECT_ROOT/services/backend"
docker build -t todo-chatbot/notification:latest "$PROJECT_ROOT/services/notification"
docker build -t todo-chatbot/recurring-task:latest "$PROJECT_ROOT/services/recurring-task"
docker build -t todo-chatbot/audit:latest "$PROJECT_ROOT/services/audit"
docker build -t todo-chatbot/frontend:latest "$PROJECT_ROOT/services/frontend"

# ── Step 7: Deploy services via Helm ─────────────────────
echo "[7/8] Deploying services..."
helm upgrade --install backend "$PROJECT_ROOT/deploy/helm/backend" \
    -n "$NAMESPACE" --wait --timeout 3m

helm upgrade --install notification "$PROJECT_ROOT/deploy/helm/notification" \
    -n "$NAMESPACE" --wait --timeout 3m

helm upgrade --install recurring-task "$PROJECT_ROOT/deploy/helm/recurring-task" \
    -n "$NAMESPACE" --wait --timeout 3m

helm upgrade --install audit "$PROJECT_ROOT/deploy/helm/audit" \
    -n "$NAMESPACE" --wait --timeout 3m

helm upgrade --install frontend "$PROJECT_ROOT/deploy/helm/frontend" \
    -n "$NAMESPACE" --wait --timeout 3m

# ── Step 8: Verify deployment ────────────────────────────
echo "[8/8] Verifying deployment..."
echo ""
echo "--- Pod Status ---"
kubectl get pods -n "$NAMESPACE"
echo ""
echo "--- Services ---"
kubectl get svc -n "$NAMESPACE"
echo ""

# Health check
BACKEND_POD=$(kubectl get pods -n "$NAMESPACE" -l app=backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
if [ -n "$BACKEND_POD" ]; then
    echo "--- Backend Health Check ---"
    kubectl exec -n "$NAMESPACE" "$BACKEND_POD" -c backend -- \
        curl -s http://localhost:8000/health || echo "  (Health check pending...)"
fi

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "Access the frontend:"
echo "  minikube service frontend-frontend -n $NAMESPACE --url"
echo ""
echo "Access the backend API:"
echo "  kubectl port-forward -n $NAMESPACE svc/backend-backend 8000:8000"
