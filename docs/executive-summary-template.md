# Executive Summary - NexusPortal

## Project Purpose

NexusPortal is a role-based internal project management application built to demonstrate secure software delivery with a DevSecOps pipeline. It gives evaluators a working business application, not only isolated security examples: users can log in, manage projects and tasks, submit feedback, and use role-based access controls.

## What Was Built

- Flask web application with Supabase/Postgres persistence and SQLite test support.
- Admin, Member, and Viewer roles.
- Login, logout, registration, and hashed password storage.
- Project and task CRUD with search and filtering.
- Feedback workflow and admin role-management panel.
- Dockerized HTTPS runtime with Gunicorn.
- GitHub Actions for SAST, SCA, DAST, and coverage evidence.

## Security Testing Performed

| Activity | Tool/Method | Outcome |
|---|---|---|
| Static analysis | Bandit, Semgrep, TruffleHog | Current Bandit and Semgrep scans report 0 app findings; TruffleHog is configured in CI |
| Dependency scanning | pip-audit, Safety | Current scans report no known vulnerable packages |
| Dynamic testing | OWASP ZAP | Baseline DAST is configured in GitHub Actions and uploads `zap-scan-report` |
| Manual testing | RBAC and business logic tests | Admin, Member, Viewer, ownership, and role-change paths tested |
| Unit/functional tests | pytest + coverage | 25 tests passed; total coverage is 83% |

## Key Risks Reviewed

- Unauthorized admin access and role escalation.
- Member access to another member's projects.
- Viewer write access.
- SQL injection through login/search forms.
- Stored XSS and server-side template injection through user content.
- Weak secret handling and insecure session cookies.
- Vulnerable dependencies and Docker runtime misconfiguration.

## Remediation Summary

The team remediated the critical and high-risk paths by enforcing server-side RBAC, parameterizing database queries, hashing passwords, clearing sessions on login/logout, requiring a production secret key, setting secure cookie flags, adding CSRF protection, applying rate limiting, adding security headers, and retesting with automated and manual checks. One medium residual risk remains: the registration page still tells users when a username or email is already registered. The application otherwise behaves as a secure project-management portal suitable for demonstration.

## Final Risk Rating

| Area | Before | After | Notes |
|---|---|---|---|
| Authentication | High | Low/Medium | SQL injection, weak secret handling, and missing rate limiting were remediated; duplicate-registration enumeration remains accepted residual risk |
| Authorization | Critical | Low | Admin-only and ownership checks are server-side and covered by tests |
| Input handling | High | Low | Validation, parameterized queries, escaping, and CSP are in place |
| Dependencies | Medium | Low | pip-audit and Safety currently report no known vulnerabilities |
| Operations | Medium | Low/Medium | Docker HTTPS runtime works; CI security scans currently archive findings for review instead of blocking every security finding |

## Recommendation

NexusPortal is ready for final demonstration after the latest report and deliverable-doc cleanup is committed. For maximum marks, the presentation should show the live app, explain one critical exploit and its fix, show the GitHub Actions security workflows, and point to the retest evidence in `REPORT.md`, `docs/images/`, and this deliverable set.
