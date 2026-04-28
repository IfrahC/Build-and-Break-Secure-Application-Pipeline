# AGENTS.md - NexusPortal Secure Application Pipeline

## Project Overview

NexusPortal is a Flask + SQLite role-based project management system for a
DevSecOps "Build and Break" assignment. The app must remain a good domain
application with working RBAC, sessions, CRUD, validation, data handling, and
security testing deliverables.

## Core Requirements

- Admin, member, and viewer users.
- Admin-only page for role management and system metrics.
- Common authenticated pages for dashboard, projects, and feedback.
- Non-admin behavior:
  - Members can create and manage only their own projects/tasks.
  - Viewers can read project information but cannot mutate data.
- Login/logout session mechanism with hashed passwords.
- Working forms, CRUD, search/filter, and basic validation.
- Dockerized runtime and GitHub Actions for SAST, SCA, DAST, and coverage.

## Commands

```bash
docker compose -f docker/docker-compose.yml up --build
python -m pytest tests -q
bandit -r app/
semgrep --config=auto \
  --exclude-rule python.django.security.django-no-csrf-token.django-no-csrf-token \
  app/
pip-audit -r app/requirements.txt
safety check -r app/requirements.txt
```

## Demo Accounts

| Role | Login |
|---|---|
| Admin | `admin@nexus.local` / `Admin1234` |
| Member | `member@nexus.local` / `Member1234` |
| Viewer | `viewer@nexus.local` / `Viewer1234` |

## Guardrails

- Keep RBAC checks server-side.
- Keep database queries parameterized.
- Keep Jinja autoescaping intact.
- Keep passwords hashed with Werkzeug.
- Keep Docker and GitHub Actions working.
- Use GitHub Issues in commit messages for traceability.
