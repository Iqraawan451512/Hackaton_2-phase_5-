#!/usr/bin/env bash
# [Task]: T086 — Cloud deployment script
# Deploys the Todo Chatbot stack to a cloud Kubernetes cluster.
#
# Prerequisites:
#   - kubectl configured for target cloud cluster
#   - helm, dapr CLI installed
#   - Docker images already pushed to registry
#
# Usage: ./deploy/cloud/deploy.sh [REGISTRY_PREFIX]
#   e.g.: ./deploy/cloud/deploy.sh ghcr.io/myorg/todo-chatbot

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NAMESPACE="todo-chatbot"
REGISTRY="${1:-ghcr.io/todo-chatbot}"
TAG="${2:-latest}"

echo "=== Todo Chatbot Cloud Deployment ==="
echo "Registry: $REGISTRY"
echo "Tag: $TAG"
echo ""

# ── Step 1: Create namespace ───────────────────────────────
echo "[1/6] Creating namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# ── Step 2: Initialize Dapr ───────────────────────────────
echo "[2/6] Ensuring Dapr is installed..."
if ! dapr status -k &>/dev/null; then
    dapr init -k --wait
fi

# ── Step 3: Deploy Kafka ─────────────────────────────────
echo "[3/6] Deploying Kafka (Redpanda, 2+ replicas)..."
helm repo add redpanda https://charts.redpanda.com 2>/dev/null || true
helm repo update
helm upgrade --install redpanda redpanda/redpanda \
    -n "$NAMESPACE" \
    -f "$PROJECT_ROOT/deploy/helm/kafka/values.yaml" \
    --set statefulset.replicas=2 \
    --wait --timeout 10m

# ── Step 4: Apply Dapr components ─────────────────────────
echo "[4/6] Applying Dapr components..."
kubectl apply -f "$PROJECT_ROOT/deploy/dapr/" -n "$NAMESPACE"

# ── Step 5: Deploy services ──────────────────────────────
echo "[5/6] Deploying services (2+ replicas)..."
SERVICES=("backend" "notification" "recurring-task" "audit" "frontend")
for svc in "${SERVICES[@]}"; do
    VALUES_FILE="$PROJECT_ROOT/deploy/helm/$svc/values-cloud.yaml"
    echo "  Deploying $svc..."
    helm upgrade --install "$svc" "$PROJECT_ROOT/deploy/helm/$svc" \
        -n "$NAMESPACE" \
        -f "$VALUES_FILE" \
        --set image.repository="$REGISTRY/$svc" \
        --set image.tag="$TAG" \
        --wait --timeout 5m
done

# ── Step 6: Verify deployment ────────────────────────────
echo "[6/6] Verifying deployment..."
echo ""
echo "--- Pod Status ---"
kubectl get pods -n "$NAMESPACE"
echo ""
echo "--- Services ---"
kubectl get svc -n "$NAMESPACE"
echo ""
echo "=== Cloud deployment complete! ==="
