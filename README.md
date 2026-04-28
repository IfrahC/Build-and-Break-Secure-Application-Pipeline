# NexusPortal - Build & Break Secure Application Pipeline

NexusPortal is a Flask + SQLite role-based project management application built
for the DevSecOps "Build and Break" assignment. It gives the group a real domain
application to design, secure, test, attack, document, remediate, and demo.

## What It Implements

| Requirement | Implementation |
|---|---|
| Domain app | Internal project and task management portal |
| RBAC | `admin`, `member`, and `viewer` roles enforced server-side |
| Admin user | Admin dashboard, role management, portfolio metrics |
| Non-admin users | Members create/manage own projects; viewers get read-only access |
| Login/logout sessions | Hashed passwords, parameterized login query, `session.clear()` on login/logout |
| Forms and inputs | Login, registration, project CRUD, task updates, feedback |
| Data handling | SQLite tables for users, projects, tasks, feedback |
| Validation | Username/email/password, project fields, task fields, feedback length/category |
| CRUD | Projects and tasks |
| Search/filter | Project search by text and status |
| Pipeline | GitHub Actions for SAST, SCA, DAST, and coverage |

## Demo Accounts

| Role | Username | Email | Password |
|---|---|---|---|
| Admin | `admin` | `admin@nexus.local` | `Admin1234` |
| Member | `member` | `member@nexus.local` | `Member1234` |
| Viewer | `viewer` | `viewer@nexus.local` | `Viewer1234` |

## Quick Start

```bash
docker compose -f docker/docker-compose.yml up --build
```

Open `http://localhost:5000`.

Run without Docker:

```bash
cd app
pip install -r requirements.txt
python app.py
```

Run tests:

```bash
python -m pytest tests -q
```

## Application Routes

| Route | Purpose | Access |
|---|---|---|
| `/` | Public landing page | Public |
| `/register` | Member registration | Public |
| `/login` | Login | Public |
| `/logout` | Logout | Authenticated |
| `/dashboard` | Role-aware summary | Authenticated |
| `/projects` | Search/filter projects | Authenticated |
| `/projects/new` | Create project | Admin, Member |
| `/projects/<id>` | Project detail and tasks | Admin, Member owner, Viewer read-only |
| `/projects/<id>/edit` | Edit project | Admin, Member owner |
| `/feedback` | Submit/review feedback | Authenticated |
| `/admin` | User role management and metrics | Admin |

## Security Pipeline

The repository includes workflows under `.github/workflows`:

- `sast.yml`: Bandit, Semgrep, TruffleHog
- `sca.yml`: pip-audit and Safety
- `dast.yml`: OWASP ZAP baseline scan against the Dockerized app
- `coverage.yml`: pytest and coverage artifacts

Local commands:

```bash
pip install bandit semgrep pip-audit safety
bandit -r app/
semgrep --config=auto \
  --exclude-rule python.django.security.django-no-csrf-token.django-no-csrf-token \
  app/
pip-audit -r app/requirements.txt
safety check -r app/requirements.txt

docker compose -f docker/docker-compose.yml up --build -d
docker run --rm -t ghcr.io/zaproxy/zaproxy \
  zap-baseline.py -t http://host.docker.internal:5000
```

## Database

SQLite database: `app/database/app.db` locally, `/app/database/app.db` in Docker.

Tables:

- `users`: username, email, hashed password, role
- `projects`: project metadata, owner, status
- `tasks`: task status, priority, assignee, due date
- `feedback`: user-submitted feedback and security observations

## Deliverables To Submit

- Architecture and threat model in `docs/threat-model-template.md`
- SAST, SCA, DAST, and coverage evidence from GitHub Actions
- Exploitation report in `docs/exploitation-report-template.md`
- Final remediation and retest report in `docs/remediation-report-template.md`
- Executive summary in `docs/executive-summary-template.md`
- GitHub Issues linked to commits, for example:

```bash
git commit -m "Fixes #12: enforce member project ownership checks"
```
