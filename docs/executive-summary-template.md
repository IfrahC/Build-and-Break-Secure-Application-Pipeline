# Executive Summary - NexusPortal

## Project Purpose

NexusPortal is a role-based internal project management application built to
demonstrate secure software delivery with a DevSecOps pipeline.

## What Was Built

- Flask web application with SQLite persistence.
- Admin, member, and viewer roles.
- Login, logout, and registration.
- Project and task CRUD.
- Search and filtering.
- Feedback/contact workflow.
- Dockerized runtime.
- GitHub Actions for SAST, SCA, DAST, and coverage.

## Security Testing Performed

| Activity | Tool/Method | Outcome |
|---|---|---|
| Static analysis | Bandit, Semgrep | `<summary>` |
| Dependency scanning | pip-audit, Safety | `<summary>` |
| Dynamic testing | OWASP ZAP | `<summary>` |
| Manual testing | RBAC and business logic tests | `<summary>` |
| Unit/functional tests | pytest | `<summary>` |

## Key Risks Reviewed

- Unauthorized role escalation.
- Member access to another member's projects.
- Viewer write access.
- Injection through forms and filters.
- Cross-site scripting through user content.
- Vulnerable dependencies.
- Container misconfiguration.

## Remediation Summary

Summarize the most important fixes and retest results in non-technical language.

## Final Risk Rating

| Area | Before | After | Notes |
|---|---|---|---|
| Authentication | `<rating>` | `<rating>` | `<notes>` |
| Authorization | `<rating>` | `<rating>` | `<notes>` |
| Input handling | `<rating>` | `<rating>` | `<notes>` |
| Dependencies | `<rating>` | `<rating>` | `<notes>` |
| Operations | `<rating>` | `<rating>` | `<notes>` |

## Recommendation

State whether NexusPortal is ready for demonstration/submission and list the top
future improvements, such as MFA, CSRF protection, rate-limiting, audit logs,
and production database migration.
