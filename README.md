# NexusPortal

A role-based internal project management web application built as part of the
**Build & Break Secure Application Pipeline** DevSecOps course assignment.

NexusPortal gives teams a real domain application to design, Dockerize, scan
with automated security tools, manually pentest, document, remediate, and demo.

---

## Table of Contents

1. [Application Overview](#application-overview)
2. [Demo Accounts](#demo-accounts)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
   - [Option A — Docker (Recommended)](#option-a--docker-recommended)
   - [Option B — Python Directly](#option-b--python-directly)
5. [Configuration](#configuration)
6. [Features & Functionality](#features--functionality)
   - [Authentication & Sessions](#authentication--sessions)
   - [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
   - [Projects](#projects)
   - [Tasks](#tasks)
   - [Feedback](#feedback)
   - [Admin Panel](#admin-panel)
   - [Dashboard](#dashboard)
7. [Application Routes](#application-routes)
8. [Database Schema](#database-schema)
9. [Directory Structure](#directory-structure)
10. [CI/CD Security Pipeline](#cicd-security-pipeline)
    - [Running Tools Locally](#running-tools-locally)
11. [Running Tests](#running-tests)
12. [Git Commit Guidelines](#git-commit-guidelines)

---

## Application Overview

NexusPortal is a Flask 3 + SQLite web application. It implements a project and
task management portal where users collaborate under strict role-based access
controls. Every route is protected server-side — the application enforces who
can see, create, edit, and delete data at the handler level, not just in the UI.

**Tech stack:**

| Layer | Technology |
|---|---|
| Web framework | Python 3.11 + Flask 3.1 |
| Database | SQLite (file-based, no separate server needed) |
| Templates | Jinja2 (auto-escaping enabled) |
| Password storage | `werkzeug.security.generate_password_hash` (scrypt) |
| Session security | `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE=Lax`, CSRF tokens |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Demo Accounts

Three seed accounts are created automatically on first run:

| Role | Username | Email | Password |
|---|---|---|---|
| Admin | `admin` | `admin@nexus.local` | `Admin1234` |
| Member | `member` | `member@nexus.local` | `Member1234` |
| Viewer | `viewer` | `viewer@nexus.local` | `Viewer1234` |

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Docker Desktop | 24+ | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| Docker Compose | v2+ | Included with Docker Desktop |
| Python | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| Git | 2.x | [git-scm.com](https://git-scm.com/) |

Python is only required for the non-Docker path or running tests locally.

---

## Installation

### Option A — Docker (Recommended)

Docker builds the image, initialises the database, and starts the app in one
command. No Python installation required on the host.

**1. Clone the repository**

```bash
git clone https://github.com/IfrahC/Build-and-Break-Secure-Application-Pipeline.git
cd Build-and-Break-Secure-Application-Pipeline
```

**2. Start the application**

```bash
docker compose -f docker/docker-compose.yml up --build
```

The first run builds the image and initialises the SQLite database. Subsequent
runs skip the build if nothing has changed:

```bash
docker compose -f docker/docker-compose.yml up
```

**3. Open in browser**

```
http://localhost:5000
```

**Stop the application**

```bash
docker compose -f docker/docker-compose.yml down
```

**Rebuild after code changes**

```bash
docker compose -f docker/docker-compose.yml up --build
```

**Inspect the database directly**

```bash
docker exec -it build-and-break-app sqlite3 /app/database/app.db
sqlite> .tables
sqlite> SELECT id, username, role FROM users;
sqlite> .quit
```

---

### Option B — Python Directly

Use this path for faster iteration during development.

**1. Clone the repository**

```bash
git clone https://github.com/IfrahC/Build-and-Break-Secure-Application-Pipeline.git
cd Build-and-Break-Secure-Application-Pipeline
```

**2. Create and activate a virtual environment**

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```bash
pip install -r app/requirements.txt
```

**4. Run the application**

```bash
cd app
python app.py
```

**5. Open in browser**

```
http://localhost:5000
```

The database file is created automatically at `app/database/app.db` on first
run with the schema and three seed accounts.

---

## Configuration

The application reads the following environment variables at startup. All have
safe defaults for local development — change them for any deployed environment.

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_SECRET_KEY` | Random `secrets.token_hex(32)` | Signs session cookies. Set a fixed value so sessions survive restarts. |
| `DATABASE_PATH` | `app/database/app.db` (local) / `/app/database/app.db` (Docker) | Path to the SQLite database file. |
| `FLASK_DEBUG` | `0` | Set to `1` to enable the Werkzeug debugger. Never use in production. |
| `FLASK_RUN_HOST` | `127.0.0.1` | Interface to bind. The Docker image sets this to `0.0.0.0`. |

**Setting a persistent secret key (Docker):**

Create a `.env` file next to `docker-compose.yml`:

```
FLASK_SECRET_KEY=replace-with-a-long-random-string
```

The compose file will pick it up automatically via the `environment` block.

---

## Features & Functionality

### Authentication & Sessions

- **Register** — new users sign up with a username, email, and password. The
  app validates format, uniqueness, minimum password length (8 characters + 1
  digit), and confirmed password match before creating the account.
- **Login** — accepts username or email. Passwords are verified with
  `check_password_hash` (scrypt). On success the session is cleared before new
  values are written (`session.clear()`), preventing session fixation.
- **Logout** — clears the entire session and redirects to the landing page.
- **CSRF protection** — every POST form includes a CSRF token generated with
  `secrets.token_urlsafe(32)` and validated server-side before processing.
- **Session cookie flags** — `HttpOnly` and `SameSite=Lax` are set at the
  application level.

### Role-Based Access Control (RBAC)

Three roles are defined and enforced with the `@roles_required` decorator on
every protected route:

| Role | What they can do |
|---|---|
| **admin** | Everything. View and manage all projects, all tasks, all feedback, all users. Change any user's role via the admin panel. |
| **member** | Create and manage their own projects and tasks. Submit feedback. Cannot access other members' projects or the admin panel. |
| **viewer** | Read-only access to all projects. Cannot create, edit, or delete anything. Can submit feedback. |

Access control is enforced **server-side** in the route handler — changing a
role in the UI or forging a request does not bypass it.

### Projects

Projects are the core entity. Each project has a title, description, status,
and an owner.

**Statuses:** `Planning` | `Active` | `Blocked` | `Completed`

| Action | Who can do it |
|---|---|
| View project list | All authenticated users |
| Search by title / description | All authenticated users |
| Filter by status | All authenticated users |
| View project detail + tasks | Admin, Member (own projects only), Viewer (read-only) |
| Create project | Admin, Member |
| Edit project | Admin, or the Member who owns it |
| Delete project | Admin, or the Member who owns it |

**Validation rules:**
- Title: 3–80 characters
- Description: 10–500 characters
- Status: must be one of the four defined values

### Tasks

Tasks belong to a project and track individual work items.

**Fields:** title, assignee (any user), status, priority, due date (optional)

**Statuses:** `Todo` | `In Progress` | `Done`

**Priorities:** `Low` | `Medium` | `High`

| Action | Who can do it |
|---|---|
| View tasks on a project | Anyone who can view the project |
| Add task | Admin, or the Member who owns the parent project |
| Update task status / priority | Admin, or the Member who owns the parent project |
| Delete task | Admin, or the Member who owns the parent project |

Tasks are ordered by priority (High first) then due date when displayed.

### Feedback

Any authenticated user can submit feedback via the `/feedback` page.

**Categories:** `Bug` | `Security` | `Feature` | `General`

| Role | What they see on `/feedback` |
|---|---|
| Admin | All feedback from all users |
| Member / Viewer | Only their own submissions |

**Validation rules:**
- Category: must be one of the four defined values
- Message: 10–500 characters

### Admin Panel

Accessible only to users with the `admin` role (`/admin`).

- View all registered users with their project count, feedback count, and role
- Change any user's role (admin / member / viewer) via a form
- Safety guard: if only one admin account exists, that admin's role cannot be
  downgraded (prevents lockout)
- View a project status breakdown summary

### Dashboard

The dashboard at `/dashboard` is role-aware:

| Role | What they see |
|---|---|
| Admin | Total projects, total users, open tasks across all projects, open feedback items, 5 most recently updated projects |
| Member | Their own project count, their open task count, their 5 most recently updated projects |
| Viewer | Open task count assigned to them, recently updated projects |

---

## Application Routes

| Method | Route | Access | Description |
|---|---|---|---|
| GET | `/` | Public | Landing page. Redirects to dashboard if logged in. |
| GET / POST | `/register` | Public | User registration form. |
| GET / POST | `/login` | Public | Login form (username or email). |
| GET | `/logout` | Authenticated | Clears session, redirects to landing. |
| GET | `/dashboard` | Authenticated | Role-aware summary page. |
| GET | `/projects` | Authenticated | Project list with search and status filter. |
| GET / POST | `/projects/new` | Admin, Member | Create a new project. |
| GET | `/projects/<id>` | Admin, Member (owner), Viewer | Project detail with task list. |
| GET / POST | `/projects/<id>/edit` | Admin, Member (owner) | Edit project title, description, status. |
| POST | `/projects/<id>/delete` | Admin, Member (owner) | Delete project and all its tasks. |
| POST | `/projects/<id>/tasks` | Admin, Member (owner) | Add a task to a project. |
| POST | `/tasks/<id>/update` | Admin, Member (project owner) | Update task status and priority. |
| POST | `/tasks/<id>/delete` | Admin, Member (project owner) | Delete a task. |
| GET / POST | `/feedback` | Authenticated | Submit feedback; admins see all submissions. |
| GET / POST | `/admin` | Admin only | User role management and system metrics. |

---

## Database Schema

The SQLite database lives at `app/database/app.db` (local) or
`/app/database/app.db` (Docker). The schema is defined in
`app/database/init.sql` and seed accounts are created by `app.py` on startup
using `generate_password_hash`.

```
users
  id            INTEGER   Primary key
  username      TEXT      Unique, 3–30 chars, letters/numbers/._-
  email         TEXT      Unique, validated format
  password_hash TEXT      scrypt hash via werkzeug
  role          TEXT      One of: admin | member | viewer
  created_at    TIMESTAMP

projects
  id            INTEGER   Primary key
  title         TEXT      3–80 chars
  description   TEXT      10–500 chars
  status        TEXT      One of: Planning | Active | Blocked | Completed
  owner_id      INTEGER   FK → users.id  (CASCADE delete)
  created_at    TIMESTAMP
  updated_at    TIMESTAMP

tasks
  id            INTEGER   Primary key
  project_id    INTEGER   FK → projects.id  (CASCADE delete)
  title         TEXT      2–120 chars
  assignee_id   INTEGER   FK → users.id  (SET NULL on delete), nullable
  status        TEXT      One of: Todo | In Progress | Done
  priority      TEXT      One of: Low | Medium | High
  due_date      TEXT      YYYY-MM-DD, nullable
  created_at    TIMESTAMP
  updated_at    TIMESTAMP

feedback
  id            INTEGER   Primary key
  user_id       INTEGER   FK → users.id  (CASCADE delete)
  category      TEXT      One of: Bug | Security | Feature | General
  message       TEXT      10–500 chars
  status        TEXT      One of: Open | Reviewed | Closed  (default Open)
  submitted_at  TIMESTAMP
```

Indexes: `projects.owner_id`, `projects.status`, `tasks.project_id`,
`feedback.user_id`.

---

## Directory Structure

```
├── app/
│   ├── app.py                   # Flask application — all routes, auth, RBAC
│   ├── __init__.py              # Package marker
│   ├── requirements.txt         # Python runtime dependencies
│   ├── database/
│   │   └── init.sql             # Schema (seeds run via app.py on startup)
│   ├── static/
│   │   ├── css/style.css        # Application stylesheet
│   │   └── js/app.js            # Minimal client-side JS
│   └── templates/
│       ├── base.html            # Base layout (nav, flash messages)
│       ├── index.html           # Public landing page
│       ├── login.html           # Login form
│       ├── register.html        # Registration form
│       ├── dashboard.html       # Role-aware dashboard
│       ├── projects.html        # Project list + search/filter
│       ├── project_form.html    # Create / edit project form
│       ├── project_detail.html  # Project detail + task management
│       ├── feedback.html        # Feedback form + list
│       └── admin.html           # Admin panel (role management)
├── docker/
│   ├── Dockerfile               # Non-root user (nexus), production-ready
│   ├── docker-compose.yml       # Compose config
│   └── docker-entrypoint.sh    # DB init + Flask startup
├── tests/
│   ├── __init__.py
│   ├── requirements-test.txt    # pytest, coverage
│   └── test_app.py              # Functional test suite
├── .github/
│   ├── workflows/
│   │   ├── sast.yml             # Bandit + Semgrep + TruffleHog
│   │   ├── sca.yml              # pip-audit + Safety (weekly schedule)
│   │   ├── dast.yml             # OWASP ZAP baseline scan
│   │   └── coverage.yml         # pytest + coverage artifacts
│   └── ISSUE_TEMPLATE/          # GitHub Issue templates
├── docs/
│   ├── threat-model-template.md
│   ├── exploitation-report-template.md
│   ├── remediation-report-template.md
│   ├── executive-summary-template.md
│   └── weekly-plan.md
├── .zap/rules.tsv               # ZAP alert suppression rules
├── .trufflehog.yml              # TruffleHog configuration
├── CONTRIBUTIONS.md             # Per-member task and commit tracking
└── README.md
```

---

## CI/CD Security Pipeline

Four GitHub Actions workflows run on push to `main` and on pull requests:

| Workflow | File | Trigger | Tools |
|---|---|---|---|
| SAST | `sast.yml` | Push / PR | Bandit, Semgrep, TruffleHog |
| SCA | `sca.yml` | Push / PR / Weekly Monday 08:00 UTC | pip-audit, Safety |
| DAST | `dast.yml` | Push to `main` / Manual dispatch | OWASP ZAP baseline |
| Coverage | `coverage.yml` | Push / PR | pytest, coverage.py |

All workflows save results as downloadable artifacts under the **Actions** tab.
Workflows do not fail the pipeline on findings — findings are captured for
analysis and reporting.

### Running Tools Locally

**SAST — Static analysis**

```bash
pip install bandit semgrep

# Bandit
bandit -r app/
bandit -r app/ -f json -o bandit-results.json

# Semgrep
semgrep --config=auto app/
semgrep --config=auto --json --output=semgrep-results.json app/
```

**SCA — Dependency scanning**

```bash
pip install pip-audit "safety<3.0.0"

# pip-audit (OSV database)
pip-audit -r app/requirements.txt

# Safety (PyUp database)
safety check -r app/requirements.txt
```

**DAST — Dynamic scanning (app must be running first)**

```bash
# Start the app
docker compose -f docker/docker-compose.yml up --build -d

# ZAP baseline scan
docker run --rm -t ghcr.io/zaproxy/zaproxy \
  zap-baseline.py -t http://host.docker.internal:5000

# ZAP full active scan with HTML report
docker run --rm -v $(pwd):/zap/wrk/:rw -t ghcr.io/zaproxy/zaproxy \
  zap-full-scan.py -t http://host.docker.internal:5000 -r zap-report.html
```

> **Linux users:** replace `host.docker.internal` with `172.17.0.1`.

---

## Running Tests

```bash
pip install -r tests/requirements-test.txt
pytest tests/ -v
```

With coverage:

```bash
pip install coverage
coverage run -m pytest tests/ -v
coverage report -m
coverage html -d coverage-html/
# Open coverage-html/index.html in a browser
```

The suite covers: public routes, registration validation, login/logout,
protected route redirects, member project CRUD, task lifecycle,
project search and filter, viewer read-only enforcement, member ownership
restrictions, admin role management, and feedback submission.

---

## Git Commit Guidelines

All commits must reference a GitHub Issue. Create the issue first, then commit
with the number in the message.

```bash
# Reference (keeps issue open)
git commit -m "Refs #5: add STRIDE table to threat model"

# Auto-close on merge to main
git commit -m "Fixes #5: complete threat model with STRIDE and risk matrix"

# Multiple issues
git commit -m "Fixes #6, #7: remediate XSS and SQL injection findings"
```

Auto-close keywords: `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`,
`resolve`, `resolves`, `resolved`.
