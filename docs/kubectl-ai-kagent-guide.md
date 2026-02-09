# AI-Assisted Kubernetes Operations Guide

## kubectl-ai and Kagent for Todo Chatbot Production Cluster

This guide demonstrates how **kubectl-ai** (AI-powered kubectl plugin) and **Kagent** (Kubernetes AI agent framework) can be used to operate, monitor, troubleshoot, and optimize the Todo Chatbot production cluster.

---

## 1. What Are These Tools?

### kubectl-ai
An AI-powered kubectl plugin that translates **natural language** into kubectl commands. Instead of memorizing complex kubectl syntax, operators describe what they want in plain English.

**Install:**
```bash
kubectl krew install ai
```

### Kagent
A Kubernetes-native AI agent framework that provides **autonomous monitoring, diagnostics, and remediation** for clusters. It runs as a controller inside the cluster and can take corrective actions.

**Install:**
```bash
helm repo add kagent https://kagent-dev.github.io/kagent
helm install kagent kagent/kagent -n kagent-system --create-namespace
```

---

## 2. Cluster Health Monitoring

### kubectl-ai Commands
```bash
# Check overall cluster health in plain English
kubectl ai "show me the health status of all pods in todo-chatbot namespace"

# Find pods that are not running or have restarts
kubectl ai "list all pods in todo-chatbot that are crashing or restarting"

# Get resource utilization summary
kubectl ai "show CPU and memory usage for all deployments in todo-chatbot"

# Check if all services have healthy endpoints
kubectl ai "are all services in todo-chatbot namespace routing to healthy pods?"

# View recent events (errors/warnings)
kubectl ai "show warning events in todo-chatbot namespace from the last hour"
```

### Kagent Monitoring Configuration
```yaml
# kagent-monitor.yaml — Autonomous health monitoring
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata:
  name: health-monitor
  namespace: todo-chatbot
spec:
  schedule: "*/5 * * * *"          # Every 5 minutes
  checks:
    - type: pod-health
      namespace: todo-chatbot
      alertOn: [CrashLoopBackOff, OOMKilled, ImagePullBackOff]
    - type: resource-usage
      thresholds:
        cpuPercent: 80
        memoryPercent: 85
  actions:
    - type: notify
      channel: slack
    - type: log
      destination: cluster-events
```

**What this does:** Kagent continuously watches all pods in the `todo-chatbot` namespace. If any pod enters a crash loop, gets OOM-killed, or exceeds 80% CPU / 85% memory, it sends alerts.

---

## 3. Auto-Scaling Based on Load

### kubectl-ai Commands
```bash
# Create HPA (Horizontal Pod Autoscaler) for backend
kubectl ai "create an autoscaler for backend-backend deployment in todo-chatbot \
  that scales between 2 and 8 replicas based on 70% CPU utilization"

# Check current autoscaler status
kubectl ai "show me the HPA status for all deployments in todo-chatbot"

# Scale frontend during peak hours
kubectl ai "scale the frontend deployment in todo-chatbot to 4 replicas"

# View scaling history
kubectl ai "show recent scaling events for deployments in todo-chatbot"
```

### Generated HPA (what kubectl-ai produces):
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: todo-chatbot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-backend
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Kagent Auto-Scaling Policy
```yaml
apiVersion: kagent.dev/v1alpha1
kind: ScalingPolicy
metadata:
  name: todo-chatbot-scaling
  namespace: todo-chatbot
spec:
  targets:
    - deployment: backend-backend
      minReplicas: 2
      maxReplicas: 8
    - deployment: frontend-frontend
      minReplicas: 2
      maxReplicas: 6
    - deployment: notification-notification
      minReplicas: 2
      maxReplicas: 4
  triggers:
    - metric: cpu_utilization
      threshold: 70
      action: scale-up
    - metric: request_latency_p95
      threshold: 500ms
      action: scale-up
    - metric: cpu_utilization
      threshold: 30
      cooldown: 10m
      action: scale-down
```

**What this does:** Kagent watches CPU and latency. When the backend hits 70% CPU or p95 latency exceeds 500ms, it scales up. When load drops below 30% for 10 minutes, it scales down.

---

## 4. Troubleshooting Failing Pods

### kubectl-ai Commands
```bash
# Diagnose why a pod is failing
kubectl ai "why is the backend pod crashing in todo-chatbot namespace?"

# Get logs from the most recent crashed pod
kubectl ai "show me logs from the last crashed backend pod in todo-chatbot"

# Check for OOM kills
kubectl ai "are any pods in todo-chatbot being killed due to memory limits?"

# Debug networking between services
kubectl ai "can the frontend pod reach the backend service on port 8000 in todo-chatbot?"

# Check Dapr sidecar status
kubectl ai "show me the Dapr sidecar container status for all pods in todo-chatbot"

# Inspect events for a specific deployment
kubectl ai "show events related to the audit deployment in todo-chatbot namespace"

# Quick describe of a problematic pod
kubectl ai "describe the most recently failed pod in todo-chatbot"
```

### Kagent Auto-Diagnostics
```yaml
apiVersion: kagent.dev/v1alpha1
kind: DiagnosticsRule
metadata:
  name: auto-troubleshoot
  namespace: todo-chatbot
spec:
  triggers:
    - event: CrashLoopBackOff
    - event: OOMKilled
    - event: ImagePullBackOff
  diagnostics:
    - collectLogs: true
      previousContainer: true
    - describeResource: true
    - checkEvents: true
    - analyzeResources: true
  remediation:
    - type: restart-pod
      condition: CrashLoopBackOff
      maxRetries: 3
    - type: increase-memory
      condition: OOMKilled
      increment: 128Mi
      maxLimit: 1Gi
  reporting:
    format: summary
    destination: operations-team
```

**What this does:** When a pod crashes, Kagent automatically collects logs, describes the resource, checks events, and analyzes resource usage. For OOM kills, it can automatically increase memory limits (up to 1Gi). For crash loops, it restarts the pod up to 3 times before alerting humans.

---

## 5. Resource Optimization

### kubectl-ai Commands
```bash
# Find over-provisioned services (wasting resources)
kubectl ai "which deployments in todo-chatbot are using less than 30% of their CPU limits?"

# Find under-provisioned services (risk of throttling)
kubectl ai "which pods in todo-chatbot are consistently above 80% memory usage?"

# Get resource recommendations
kubectl ai "suggest optimal CPU and memory limits for all deployments in todo-chatbot \
  based on the last 7 days of usage"

# Identify idle replicas
kubectl ai "are there any replicas in todo-chatbot that received zero traffic in the last hour?"

# Cost analysis
kubectl ai "estimate the monthly compute cost for the todo-chatbot namespace"
```

### Kagent Resource Optimizer
```yaml
apiVersion: kagent.dev/v1alpha1
kind: ResourceOptimizer
metadata:
  name: todo-chatbot-optimizer
  namespace: todo-chatbot
spec:
  analysisWindow: 7d
  targets:
    - namespace: todo-chatbot
  recommendations:
    - type: right-size
      strategy: percentile95
      buffer: 20%            # Add 20% headroom above p95 usage
    - type: consolidate
      minUtilization: 30%    # Flag resources below 30% utilization
  reporting:
    schedule: "0 9 * * 1"   # Weekly Monday 9AM report
    format: table
    destination: operations-team
```

**What this does:** Kagent analyzes 7 days of resource usage, calculates p95 usage, adds 20% headroom, and recommends optimal CPU/memory limits. Generates weekly reports flagging over/under-provisioned services.

---

## 6. Quick Reference: Common Operations

| Task | kubectl-ai Command |
|------|-------------------|
| View all pods | `kubectl ai "list all pods in todo-chatbot with their status"` |
| Check logs | `kubectl ai "show last 50 log lines from backend pod"` |
| Restart service | `kubectl ai "restart the notification deployment in todo-chatbot"` |
| Check secrets | `kubectl ai "list all secrets in todo-chatbot namespace"` |
| Port forward | `kubectl ai "forward port 8000 from backend pod to my localhost"` |
| Rollback | `kubectl ai "rollback the backend deployment to previous version"` |
| Node pressure | `kubectl ai "are any nodes under memory or disk pressure?"` |
| Network policy | `kubectl ai "show network policies affecting todo-chatbot"` |

---

## 7. Production Workflow Summary

```
Developer pushes to master
        |
GitHub Actions builds & pushes images to GHCR
        |
Helm deploys to Kubernetes cluster
        |
  +-----+------+
  |            |
kubectl-ai   Kagent
(on-demand)  (autonomous)
  |            |
  +-----+------+
        |
  Monitor → Detect → Diagnose → Remediate → Optimize
```

**kubectl-ai** = Human-in-the-loop AI operations (ask questions, get answers)
**Kagent** = Autonomous AI operations (watches, detects, fixes automatically)

Together they provide a complete AI-assisted operations layer for the Todo Chatbot production cluster.
