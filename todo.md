# DevSecOps Project — TODO

> **30 Students · 10 Groups · 3 Members per Group**
> One shared GitHub repo per group. All commits must follow the issue-association format: `fix #12: sanitise SQL input in login form`

---

## Group Setup

- [ ] Form groups of 3 and register with instructor
- [ ] Create a shared GitHub repository
- [ ] Assign roles (e.g. App Dev / Security / Report lead)
- [ ] Document roles in README or wiki
- [ ] Set up GitHub Issues, Labels, and Milestones for each week
- [ ] Configure branch strategy (feature branches + PRs, no direct pushes to `main`)

---

## Application Baseline (Required to Unlock Full Marks on Criteria 04–06)

- [ ] App runs on a hostname/IP with **HTTPS** (self-signed or real cert — not localhost)
- [ ] **RBAC** implemented: admin role + non-admin role
  - [ ] Admin-only pages are truly restricted
  - [ ] Non-admin users cannot access admin routes
- [ ] Login / Logout with proper session management
- [ ] **CRUD** operations all working (Create, Read, Update, Delete)
- [ ] Search / Filter functionality
- [ ] Input validation on all forms
- [ ] Database connected and persisting data
- [ ] Home / Dashboard page
- [ ] Main feature page
- [ ] Login / Register page

---

## Week 1 — Design & Threat Modelling

- [ ] Define the application domain and core features
- [ ] Design the architecture (frontend / backend / database layers)
- [ ] Draw a **Data Flow Diagram (DFD)** with actors, data flows, and trust boundaries
- [ ] Apply **STRIDE** to each component
- [ ] Score threats using **DREAD or CVSS**
- [ ] Build a threat prioritisation matrix
- [ ] Define and document the attack surface
- [ ] Open GitHub Issues for all Week 1 tasks before starting work
- [ ] Push all design documents to the repo with linked issues

---

## Week 2 — Build, Dockerize & SAST/SCA

### Application Build
- [ ] Build all baseline features (RBAC, CRUD, sessions, validation)
- [ ] Connect and seed the database
- [ ] Verify app runs correctly on HTTPS hostname (not localhost)

### Dockerization
- [ ] Write `Dockerfile` for the application
- [ ] Write `docker-compose.yml` (app + database)
- [ ] Add installation guide and `README.md` with setup instructions

### CI/CD Pipeline (GitHub Actions)
- [ ] Create pipeline config file (`.github/workflows/`)
- [ ] Configure pipeline to trigger on `push` and `pull_request` events
- [ ] **SAST** — integrate a static analysis tool (e.g. Semgrep, Bandit, CodeQL)
  - [ ] Reports archived as pipeline artifacts
- [ ] **SCA** — integrate a dependency scanner (e.g. Dependabot, OWASP Dependency-Check, Trivy)
  - [ ] Reports archived as pipeline artifacts
- [ ] Add a deployment step (spin up Docker app in CI)
- [ ] Open GitHub Issues for all Week 2 tasks before starting work

---

## Week 3 — DAST & Manual Pentesting

### DAST Integration
- [ ] **DAST** — integrate a dynamic analysis tool (e.g. OWASP ZAP, Nuclei)
  - [ ] Dockerized app spun up for DAST in CI
  - [ ] Reports archived as pipeline artifacts
- [ ] Configure pipeline to **fail on critical/high severity findings** (quality gate)
- [ ] Ensure all three stages — SAST + DAST + SCA — are running in the pipeline

### Vulnerability Discovery
- [ ] Review and filter automated tool output (exclude false positives)
- [ ] Map all findings to **OWASP Top 10**
- [ ] Calculate **CVSS v3.1 scores** with vector strings for each finding
- [ ] Capture screenshots and HTTP request evidence for each finding
- [ ] Perform **manual pentesting**:
  - [ ] Test for business logic flaws (IDOR, broken RBAC, etc.)
  - [ ] Test for chained / multi-step vulnerabilities
  - [ ] Test authentication and session handling
  - [ ] Test for injection points (SQLi, XSS, etc.)

### Exploitation
- [ ] Exploit at least the critical/high findings with a working PoC
- [ ] Document step-by-step reproduction steps for each exploit
- [ ] Capture screenshots demonstrating real impact (data leakage, privilege escalation, etc.)
- [ ] Quantify business impact where possible
- [ ] Open GitHub Issues for all Week 3 tasks before starting work

---

## Week 4 — Remediation, Report & Presentation

### Fixes
- [ ] Remediate all critical and high findings at root-cause level
- [ ] Commit fixes to a dedicated remediation branch
- [ ] Re-run pipeline after fixes — confirm it **passes** quality gates
- [ ] Re-test each fixed finding and capture evidence (screenshots / pipeline output)
- [ ] Add regression checks or unit tests where applicable
- [ ] Formally accept any remaining low/informational risks with written rationale

### Report
- [ ] **Table of Contents** — all sections, subsections, appendices; functional hyperlinks
- [ ] **Executive Summary** — risk summary, business impact, recommendations (non-technical language)
- [ ] **Architecture & Threat Model** — DFD, STRIDE table, prioritisation matrix
- [ ] **Vulnerability Findings Table** — severity, CVSS score, OWASP mapping, status
- [ ] **Exploitation Evidence** — PoC steps, screenshots, payloads
- [ ] **Remediation Evidence** — code diffs, re-test screenshots, pipeline output
- [ ] **Annexes** — raw tool output, additional screenshots
- [ ] Proofread the entire report (grammar, consistency, formatting)

### Presentation & Live Demo
- [ ] All 3 members prepare to present their own section
- [ ] Live demo includes: full app walkthrough + live attack + fix proof
- [ ] Show pipeline running live (or recorded output)
- [ ] Executive summary deliverable in plain language
- [ ] HTTPS confirmed working for demo
- [ ] Rehearse Q&A — each member must explain their own commits and findings

---

## GitHub Hygiene (Ongoing — All 4 Weeks)

- [ ] Every task has a GitHub Issue created **before** work begins
- [ ] All commits follow format: `fix #N: short description`
- [ ] Issues closed via commit references (`fixes #N`)
- [ ] Use milestones for each week
- [ ] Use labels (e.g. `sast`, `dast`, `report`, `fix`, `vuln`)
- [ ] Use pull requests with review comments for merging
- [ ] All 3 members contributing commits throughout all 4 weeks

---

## Grading Checklist (Self-Assessment Before Submission)

| # | Criterion | Marks | Done? |
|---|-----------|-------|-------|
| 01 | Table of Contents | 5 | ☐ |
| 02 | Architecture & Threat Model | 5 | ☐ |
| 03 | GitHub Pipeline Implementation | 10 | ☐ |
| 04 | Vulnerability Discovery Depth | 20 | ☐ |
| 05 | Exploitation Quality | 10 | ☐ |
| 06 | Remediation Effectiveness | 10 | ☐ |
| 07 | Report Quality | 5 | ☐ |
| 08 | GitHub Issues, Pushes & Updates | 5 | ☐ |
| 09 | Member Contributions & GitHub Profiles | 5 | ☐ |
| 10 | Presentation & Live Demo | 25 | ☐ |
| | **Total** | **100** | |

> **70% Group Mark** — shared repository, report, pipeline, findings (Criteria 01–09)
> **30% Individual Viva Mark** — live presentation, Q&A on your own work (Criterion 10)

---

## AI Usage Reminder

- AI tools are permitted for development and tooling assistance
- You **must** be able to explain every vulnerability, exploit, and fix in your own words during the viva
- AI-assisted code with unreported security flaws counts against Criterion 04
