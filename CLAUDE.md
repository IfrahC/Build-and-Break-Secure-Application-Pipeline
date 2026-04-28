# CLAUDE.md - NexusPortal Secure Application Pipeline

## Project Overview

NexusPortal is a Python Flask + SQLite RBAC project management application for a
DevSecOps course. It is designed to satisfy the professor's requirement for a
real domain app with admin and non-admin pages, working sessions, CRUD,
validation, data storage/retrieval, and a full security testing pipeline.

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | Python 3.11 + Flask 3.1 |
| Database | SQLite |
| Templates | Jinja2 |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| SAST | Bandit, Semgrep, TruffleHog |
| SCA | pip-audit, Safety |
| DAST | OWASP ZAP |
| Tests | pytest + coverage |

## Key Commands

```bash
docker compose -f docker/docker-compose.yml up --build
cd app && pip install -r requirements.txt && python app.py
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

## RBAC Rules

- Admin can view all projects, manage roles, manage all projects/tasks, and view all feedback.
- Member can create projects and manage only projects they own.
- Viewer can view project information but cannot create, edit, or delete.
- All protected routes must use `login_required` or `roles_required`.
- Authorization must be checked server-side; hiding buttons in templates is not enough.

## Application Routes

| Route | Access |
|---|---|
| `/`, `/login`, `/register` | Public |
| `/dashboard`, `/projects`, `/feedback`, `/logout` | Authenticated |
| `/projects/new`, `/projects/<id>/edit`, project/task mutations | Admin or owning Member |
| `/admin` | Admin only |

## Do Not Regress

- Do not store plaintext passwords.
- Do not build SQL using user-controlled string interpolation.
- Do not render user content with `| safe`.
- Do not remove `session.clear()` from login/logout.
- Do not rely on client-side role checks.
- Do not pin dependencies to known vulnerable versions for the final submission.
