#!/usr/bin/env bash
# [Task]: T083 — Minikube smoke test: verify all pods and end-to-end flow
# Run this after deploy.sh to validate the deployment.
#
# Usage: ./deploy/minikube/smoke-test.sh

set -euo pipefail

NAMESPACE="todo-chatbot"
BACKEND_URL="http://localhost:8000"
PASS=0
FAIL=0

echo "=== Todo Chatbot Smoke Test ==="

# ── Check pods have 2/2 containers (app + Dapr sidecar) ──
echo ""
echo "[1/5] Checking pod status..."
SERVICES=("backend" "notification" "recurring-task" "audit" "frontend")
for svc in "${SERVICES[@]}"; do
    STATUS=$(kubectl get pods -n "$NAMESPACE" -l app="$svc" -o jsonpath='{.items[0].status.containerStatuses[*].ready}' 2>/dev/null || echo "")
    if echo "$STATUS" | grep -q "true true"; then
        echo "  ✓ $svc: 2/2 containers ready"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $svc: NOT ready (status: $STATUS)"
        FAIL=$((FAIL + 1))
    fi
done

# ── Health checks ─────────────────────────────────────────
echo ""
echo "[2/5] Running health checks..."
# Port-forward backend in background
kubectl port-forward -n "$NAMESPACE" svc/backend-backend 8000:8000 &
PF_PID=$!
sleep 3

HEALTH=$(curl -s "$BACKEND_URL/health" || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  ✓ Backend /health: OK"
    PASS=$((PASS + 1))
else
    echo "  ✗ Backend /health: FAILED ($HEALTH)"
    FAIL=$((FAIL + 1))
fi

# ── Create a task ─────────────────────────────────────────
echo ""
echo "[3/5] Testing task creation..."
CREATE_RESP=$(curl -s -X POST "$BACKEND_URL/api/tasks" \
    -H "Content-Type: application/json" \
    -H "X-User-ID: smoke-test-user" \
    -d '{"title":"Smoke test task","priority":"high","tags":["smoke-test"]}')

TASK_ID=$(echo "$CREATE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
if [ -n "$TASK_ID" ]; then
    echo "  ✓ Task created: $TASK_ID"
    PASS=$((PASS + 1))
else
    echo "  ✗ Task creation failed: $CREATE_RESP"
    FAIL=$((FAIL + 1))
fi

# ── Complete the task ─────────────────────────────────────
echo ""
echo "[4/5] Testing task completion..."
if [ -n "$TASK_ID" ]; then
    COMPLETE_RESP=$(curl -s -X POST "$BACKEND_URL/api/tasks/$TASK_ID/complete" \
        -H "X-User-ID: smoke-test-user")
    STATUS=$(echo "$COMPLETE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
    if [ "$STATUS" = "completed" ]; then
        echo "  ✓ Task completed successfully"
        PASS=$((PASS + 1))
    else
        echo "  ✗ Task completion failed: $COMPLETE_RESP"
        FAIL=$((FAIL + 1))
    fi
else
    echo "  ✗ Skipped (no task ID)"
    FAIL=$((FAIL + 1))
fi

# ── List tasks ────────────────────────────────────────────
echo ""
echo "[5/5] Testing task listing..."
LIST_RESP=$(curl -s "$BACKEND_URL/api/tasks" \
    -H "X-User-ID: smoke-test-user")
if echo "$LIST_RESP" | python3 -c "import sys,json; data=json.load(sys.stdin); assert isinstance(data, list)" 2>/dev/null; then
    echo "  ✓ Task listing works"
    PASS=$((PASS + 1))
else
    echo "  ✗ Task listing failed: $LIST_RESP"
    FAIL=$((FAIL + 1))
fi

# Cleanup
kill $PF_PID 2>/dev/null || true

# ── Summary ───────────────────────────────────────────────
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All smoke tests passed!"
