# Contributions — [Group Name / Number]

> **Course:** DevSecOps Pipeline  
> **Group:** [Group Number]  
> **Members:** [List all 3 names]

All contributions are traceable via GitHub commits linked to Issues.
Run `git log --author="<name>"` to filter commits by individual.

---

## Team Members & Responsibilities

| Member | Student ID | Primary Areas |
|--------|-----------|---------------|
| [Name 1] | [ID] | Application development, SAST analysis |
| [Name 2] | [ID] | Docker, CI/CD pipeline, DAST |
| [Name 3] | [ID] | Threat model, exploitation report, remediation |

---

## Week 1 — Design & Threat Model

| Task | Assigned To | GitHub Issue | Commit(s) |
|------|------------|-------------|-----------|
| Data Flow Diagram | | | |
| STRIDE threat table | | | |
| Risk matrix | | | |
| Attack surface mapping | | | |

---

## Week 2 — Build & SAST / SCA

| Task | Assigned To | GitHub Issue | Commit(s) |
|------|------------|-------------|-----------|
| Bandit scan + documentation | | | |
| Semgrep scan + documentation | | | |
| pip-audit scan + documentation | | | |
| Safety scan + documentation | | | |
| GitHub Actions verification | | | |

---

## Week 3 — DAST & Manual Pentesting

| Task | Assigned To | GitHub Issue | Commit(s) |
|------|------------|-------------|-----------|
| ZAP baseline scan | | | |
| ZAP full scan | | | |
| SQLi exploitation (VULN-2) | | | |
| XSS exploitation (VULN-3) | | | |
| IDOR exploitation (VULN-4) | | | |
| Path traversal exploitation (VULN-5) | | | |
| Broken auth documentation (VULN-6) | | | |
| Exploitation report draft | | | |

---

## Week 4 — Remediation & Reporting

| Task | Assigned To | GitHub Issue | Commit(s) |
|------|------------|-------------|-----------|
| Fix VULN-1 (hardcoded secrets) | | | |
| Fix VULN-2 (SQL injection) | | | |
| Fix VULN-3 (XSS) | | | |
| Fix VULN-4 (IDOR) | | | |
| Fix VULN-5 (path traversal) | | | |
| Fix VULN-6 (session fixation) | | | |
| Fix VULN-7 (password logging) | | | |
| Fix VULN-8 (dependency CVE) | | | |
| Remediation report | | | |
| Executive summary | | | |
| Presentation preparation | | | |

---

## Commit Attribution

To view commits by a specific team member:

```bash
git log --author="Name" --oneline
```

To see all commits with associated issues:

```bash
git log --oneline --grep="Fixes\|Refs\|Closes"
```

All commits follow the format:
```
Fixes #<issue>: <short description>
```
