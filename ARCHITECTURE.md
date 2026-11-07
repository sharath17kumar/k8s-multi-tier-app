# Kubernetes Multi-Tier Application - Architecture

## System Overview

Client (Browser)
    |
    | HTTP :30080
    v
+-------------------+
|  Frontend         |
|  (Nginx:alpine)   |
|  Deployment: 1    |
|  Service: NodePort|
+-------------------+
    |
    | /api/* proxy_pass
    | (Kubernetes DNS: backend-service:5000)
    v
+-------------------+
|  Backend API      |
|  (Flask+Gunicorn) |
|  Deployment: 2    |
|  Service: ClusterIP|
|  Probes: liveness |
|    + readiness    |
|  Exposes: /metrics|
+-------------------+
    |
    | psycopg2 connection
    | (Kubernetes DNS: postgres-service:5432)
    v
+-------------------+
|  PostgreSQL 16    |
|  StatefulSet: 1   |
|  Service: Headless|
|  PVC: 1Gi storage |
|  Config: ConfigMap|
|  Password: Secret |
+-------------------+

## Monitoring Stack

+-------------------+       +-------------------+
|  Prometheus       |<------| Backend /metrics  |
|  Scrapes every 15s|       | (app metrics)     |
|  Service: NodePort|       +-------------------+
|  Port: 30090      |
+-------------------+
    |
    | Data source
    v
+-------------------+
|  Grafana          |
|  Dashboards       |
|  Service: NodePort|
|  Port: 30030      |
+-------------------+

## Automation Layer

scripts/
  cluster-health.sh    -> Full cluster health report
  pod-monitor.py       -> Auto-scaling based on CPU metrics
  incident-response.sh -> Debug info collection during outages

## Key Design Decisions

1. StatefulSet for PostgreSQL (not Deployment)
   - Stable network identity (postgres-0)
   - Persistent storage survives pod restarts

2. Deployment for Backend (not StatefulSet)
   - Stateless - any replica handles any request
   - Easy horizontal scaling

3. ConfigMap + Secret for configuration
   - Separates config from code (12-factor app)
   - Secrets are base64 encoded, can be encrypted

4. Liveness + Readiness probes
   - Self-healing: crashed pods restart automatically
   - Zero-downtime deployments: traffic only hits ready pods

5. Headless Service for PostgreSQL
   - Direct pod DNS (postgres-0.postgres-service)
   - No load balancing (databases need direct connections)

6. NodePort Services for external access
   - Frontend: 30080, Prometheus: 30090, Grafana: 30030
   - In production: replaced with LoadBalancer or Ingress

## Technologies Used

| Layer          | Technology        | Why                                    |
|----------------|-------------------|----------------------------------------|
| Frontend       | Nginx Alpine      | Lightweight, fast static file serving  |
| Backend        | Flask + Gunicorn  | Simple API + production WSGI server    |
| Database       | PostgreSQL 16     | Reliable, ACID-compliant RDBMS        |
| Container      | Docker            | Consistent packaging across environments|
| Orchestration  | Kubernetes        | Auto-healing, scaling, rolling updates |
| Metrics        | Prometheus        | Pull-based monitoring, time-series DB  |
| Visualization  | Grafana           | Dashboards, alerting, data exploration |
| Scripting      | Bash + Python     | Automation, monitoring, incident response|
