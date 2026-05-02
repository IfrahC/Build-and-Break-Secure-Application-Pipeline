# Contributions - NexusPortal

> **Course:** DevSecOps Pipeline  
> **Project:** Build and Break Secure Application Pipeline  
> **Members:** Ifrah, Bilal, Sabahat

All implementation work is traceable through GitHub Issues and issue-linked
commits on the `main` branch.

## Team Members & Responsibilities

| Member | Student ID | Primary Areas |
|--------|------------|---------------|
| Ifrah | Add ID | Repository ownership, GitHub Issues, report coordination, presentation review |
| Bilal | Add ID | Flask application implementation, RBAC, tests, Git/GitHub workflow cleanup |
| Sabahat | Add ID | Threat model, security testing evidence, exploitation/remediation reporting |

## Issue And Commit Traceability

| GitHub Issue | Purpose | Commit |
|--------------|---------|--------|
| #1 - Build NexusPortal RBAC domain application | Flask app, RBAC, sessions, SQLite, CRUD, validation, UI pages | `ac7c410` - `Fixes #1: build NexusPortal RBAC portal` |
| #2 - Add functional tests for RBAC workflows | pytest coverage for auth, RBAC, CRUD, search/filter, feedback, tasks | `61be1ae` - `Fixes #2: add NexusPortal RBAC functional tests` |
| #3 - Align Docker and security pipeline for NexusPortal | Docker, SAST, SCA, DAST, coverage workflow alignment | `13f7616` - `Fixes #3: align Docker and security pipeline for NexusPortal` |
| #4 - Update project documentation and report templates | README, weekly plan, threat model, exploitation, remediation, executive summary templates | `2f46e75` - `Fixes #4: document NexusPortal deliverables and reports` |

## Week 1 - Design & Threat Model

| Task | Assigned To | GitHub Issue | Evidence / Commit |
|------|-------------|--------------|-------------------|
| Define NexusPortal domain and roles | Ifrah, Bilal | #1 | `README.md`, `app/app.py`, `ac7c410` |
| Map attack surface | Sabahat | #4 | `docs/threat-model-template.md`, `2f46e75` |
| Prepare STRIDE threat model structure | Sabahat | #4 | `docs/threat-model-template.md`, `2f46e75` |
| Confirm required pages and access levels | Bilal | #1 | `/dashboard`, `/projects`, `/admin`, `/feedback`, `ac7c410` |

## Week 2 - Build, Dockerize, SAST/SCA

| Task | Assigned To | GitHub Issue | Evidence / Commit |
|------|-------------|--------------|-------------------|
| Build login/register/logout session flow | Bilal | #1 | `app/app.py`, `ac7c410` |
| Build server-side RBAC checks | Bilal | #1 | `roles_required`, ownership checks, `ac7c410` |
| Build project/task CRUD and search/filter | Bilal | #1 | `projects`, `project_detail`, task routes, `ac7c410` |
| Add SQLite schema and seed users | Bilal | #1 | `app/database/init.sql`, `ac7c410` |
| Add functional tests | Bilal | #2 | `tests/test_app.py`, `61be1ae` |
| Configure Docker runtime | Ifrah, Bilal | #3 | `docker/Dockerfile`, `docker/docker-compose.yml`, `13f7616` |
| Run and verify SAST/SCA workflows | Ifrah, Sabahat | #3 | GitHub Actions SAST/SCA successful runs, `13f7616` |

## Week 3 - DAST & Manual Security Testing

| Task | Assigned To | GitHub Issue | Evidence / Commit |
|------|-------------|--------------|-------------------|
| Run OWASP ZAP baseline DAST workflow | Sabahat | #3 | GitHub Actions DAST successful run |
| Verify admin-only page protection | Sabahat | #2 | `test_admin_can_access_admin_page_and_update_roles`, `61be1ae` |
| Verify viewer read-only restrictions | Sabahat | #2 | `test_viewer_has_read_only_project_access`, `61be1ae` |
| Verify member ownership restrictions | Sabahat | #2 | `test_member_cannot_view_other_member_project`, `61be1ae` |
| Verify invalid login and registration validation | Bilal, Sabahat | #2 | auth/register tests, `61be1ae` |
| Capture evidence for exploitation/business-logic testing | Sabahat | #4 | `docs/exploitation-report-template.md`, screenshots to be added |

## Week 4 - Remediation, Retest & Reporting

| Task | Assigned To | GitHub Issue | Evidence / Commit |
|------|-------------|--------------|-------------------|
| Add password hashing and safe session handling | Bilal | #1 | `generate_password_hash`, `session.clear`, `ac7c410` |
| Add CSRF protection for POST forms | Bilal | #1 | `csrf_token`, `validate_csrf_token`, templates, `ac7c410` |
| Add parameterized database queries | Bilal | #1 | SQLite `?` parameters throughout `app/app.py`, `ac7c410` |
| Retest with pytest and coverage | Bilal | #2 | GitHub Actions Coverage successful run |
| Retest with SAST, SCA, and DAST | Ifrah, Sabahat | #3 | GitHub Actions SAST/SCA/DAST successful runs |
| Complete remediation and retest report | Sabahat | #4 | `docs/remediation-report-template.md`, `2f46e75` |
| Complete executive summary | Ifrah | #4 | `docs/executive-summary-template.md`, `2f46e75` |
| Prepare live presentation/demo | All members | #4 | README demo accounts, Actions screenshots, report evidence |

## GitHub Evidence Commands

View issue-linked commits:

```bash
git log --oneline --grep="Fixes\|Refs\|Closes"
```

View commits by author:

```bash
git log --author="Bilal" --oneline
git log --author="Ifrah" --oneline
git log --author="Sabahat" --oneline
```

> Note: Some group work may be represented through issues, reports, screenshots,
> and presentation evidence rather than direct code commits if one member handled
> Git operations on behalf of the team.
