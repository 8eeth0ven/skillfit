---
name: deployment-router
description: Route deployment and operational work through environment, authorization, risk, rollback, verification, monitoring, and record gates. Use for deploy, release promotion, environment variables, infrastructure, CI/CD, scheduled jobs, production data, permissions, or service recovery.
---

# Deployment Router

1. Identify target environment, version, service, account, data sensitivity, blast radius, maintenance window, and required authorization.
2. Read the approved Plan, architecture, deployment docs, current production identity, open risks, and rollback procedure.
3. Verify secrets are supplied through approved channels and never written to logs or records.
4. Prepare backup, migration, health checks, smoke tests, monitoring, and rollback trigger before mutation.
5. Require explicit user authorization for production, destructive data changes, real transactions, permission changes, external notifications, or irreversible operations.
6. Execute the smallest reversible steps, verify after each step, and stop on unexpected scope expansion.
7. Update operations, issue, risk, acceptance, task, Plan, and version records with evidence.

Do not interpret code readiness as deployment authorization, and do not auto-deploy from a Hook.
