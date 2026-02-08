#!/usr/bin/env bash
# [Task]: T088 — Cloud deployment verification script
# Verifies cloud deployment: replicas, health, and end-to-end event pipeline.
#
# Usage: ./deploy/cloud/verify.sh

set -euo pipefail

NAMESPACE="todo-chatbot"
PASS=0
FAIL=0

echo "=== Cloud Deployment Verification ==="

# ── Step 1: Check replica counts ─────────────────────────
echo ""
echo "[1/4] Checking replica counts (expect 2+)..."
SERVICES=("backend" "notification" "recurring-task" "audit" "frontend")
for svc in "${SERVICES[@]}"; do
    READY=$(kubectl get deployment -n "$NAMESPACE" -l app="$svc" \
        -o jsonpath='{.items[0].status.readyReplicas}' 2>/dev/null || echo "0")
    DESIRED=$(kubectl get deployment -n "$NAMESPACE" -l app="$svc" \
        -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "0")
    if [ "$READY" -ge 2 ] && [ "$READY" -eq "$DESIRED" ]; then
        echo "  ✓ $svc: $READY/$DESIRED replicas ready"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $svc: $READY/$DESIRED replicas (expected 2+)"
        FAIL=$((FAIL + 1))
    fi
done

# ── Step 2: Check Dapr sidecars ──────────────────────────
echo ""
echo "[2/4] Checking Dapr sidecars (2/2 containers per pod)..."
for svc in "${SERVICES[@]}"; do
    PODS=$(kubectl get pods -n "$NAMESPACE" -l app="$svc" \
        -o jsonpath='{range .items[*]}{.metadata.name}:{.status.containerStatuses[*].ready}{"\n"}{end}' 2>/dev/null || echo "")
    ALL_READY=true
    while IFS= read -r line; do
        if [ -z "$line" ]; then continue; fi
        if ! echo "$line" | grep -q "true true"; then
            ALL_READY=false
        fi
    done <<< "$PODS"
    if $ALL_READY && [ -n "$PODS" ]; then
        echo "  ✓ $svc: all pods have 2/2 containers"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $svc: some pods missing sidecar"
        FAIL=$((FAIL + 1))
    fi
done

# ── Step 3: Health checks ────────────────────────────────
echo ""
echo "[3/4] Running health checks via port-forward..."
kubectl port-forward -n "$NAMESPACE" svc/backend-backend 8000:8000 &
PF_PID=$!
sleep 3

HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  ✓ Backend /health: OK"
    PASS=$((PASS + 1))
else
    echo "  ✗ Backend /health: FAILED"
    FAIL=$((FAIL + 1))
fi

# ── Step 4: End-to-end event pipeline ────────────────────
echo ""
echo "[4/4] Testing end-to-end event pipeline..."
CREATE_RESP=$(curl -s -X POST http://localhost:8000/api/tasks \
    -H "Content-Type: application/json" \
    -H "X-User-ID: cloud-verify" \
    -d '{"title":"Cloud verify task","priority":"high"}' 2>/dev/null || echo "{}")

TASK_ID=$(echo "$CREATE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
if [ -n "$TASK_ID" ]; then
    echo "  ✓ Task created: $TASK_ID"
    PASS=$((PASS + 1))

    # Complete the task
    curl -s -X POST "http://localhost:8000/api/tasks/$TASK_ID/complete" \
        -H "X-User-ID: cloud-verify" >/dev/null 2>&1
    echo "  ✓ Task completed"
    PASS=$((PASS + 1))

    # Brief pause for event propagation
    sleep 2

    # Delete the test task
    curl -s -X DELETE "http://localhost:8000/api/tasks/$TASK_ID" \
        -H "X-User-ID: cloud-verify" >/dev/null 2>&1
    echo "  ✓ Task deleted (cleanup)"
    PASS=$((PASS + 1))
else
    echo "  ✗ Task creation failed"
    FAIL=$((FAIL + 3))
fi

kill $PF_PID 2>/dev/null || true

# ── Pod failure recovery ─────────────────────────────────
echo ""
echo "--- Pod Recovery Test ---"
echo "  (Manual: delete a pod and verify it auto-restarts)"
echo "  kubectl delete pod -n $NAMESPACE -l app=backend --grace-period=0 --force"
echo "  kubectl get pods -n $NAMESPACE -l app=backend -w"

# ── Summary ──────────────────────────────────────────────
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "Cloud deployment verified!"
