# Remediation and Retest Report - NexusPortal

## Summary

The remediation phase fixed the root causes behind authentication bypass, broken access control, insecure session configuration, injection risks, unsafe rendering, missing headers, weak rate limiting, username enumeration, and role disclosure. Retesting confirms the application now enforces RBAC server-side, uses parameterized queries, stores hashed passwords, validates forms, protects POST routes with CSRF tokens, sets secure session cookies, and runs clean SAST/SCA checks.

## Remediation Tracker

| Issue | Finding | Fix Summary | Commit / Evidence | Retest Result |
|---|---|---|---|---|
| #1 | SQL injection login bypass | Parameterized login query and password hash verification | `ac7c410` | Pass |
| #2 | Insecure secret-key handling | Require persistent `FLASK_SECRET_KEY` in production | `c929ab0` | Pass |
| #3 | Admin route bypass | `@roles_required("admin")` on `/admin` | `ac7c410` | Pass |
| #4 | IDOR on projects/tasks | Ownership checks before view/edit/delete/task mutation | `ac7c410` | Pass |
| #5 | Stored XSS | Jinja autoescape, no unsafe user-content rendering, CSP header | `e437485` | Pass |
| #6 | SSTI | Feedback rendered through static templates as escaped data | `ac7c410` | Pass |
| #7 | Vulnerable dependencies | Current Flask/Werkzeug/Jinja versions scan clean | `13f7616` | Pass |
| #8 | Debug mode in production | Docker sets `FLASK_ENV=production` and `FLASK_DEBUG=0` | `13f7616` | Pass |
| #9 | Insecure session cookie | Set `Secure`, `HttpOnly`, and `SameSite=Lax` flags | `0173900` | Pass |
| #10 | No auth rate limiting | Flask-Limiter on login/register POST routes | `354bca7` | Pass |
| #11 | Chained admin escalation | Combined RBAC, rate limiting, session, and auth hardening | `604049b` | Pass |
| #12 | Missing security headers | Added XFO, CSP, nosniff, and referrer-policy headers | `e437485` | Pass |
| #13 | Username enumeration | Duplicate warning retained for usability; residual risk documented with compensating controls | Accepted residual | Accepted |
| #14 | Role disclosure | Assignee dropdown no longer exposes user roles | `8ceebfc`, `58bd3c4` | Pass |

## Retest Commands

```bash
python -m pytest tests -q
python -m coverage run --source=app -m pytest tests -q
python -m coverage report -m
python -m bandit -r app/
semgrep --config=auto --exclude-rule python.django.security.django-no-csrf-token.django-no-csrf-token app/
pip-audit -r app/requirements.txt
safety check -r app/requirements.txt
docker build -f docker/Dockerfile -t nexusportal-audit .
curl -k -I https://localhost:5000
```

## Current Retest Results

| Check | Result |
|---|---|
| pytest | 25 passed |
| coverage | 83% total coverage |
| Bandit | 0 issues |
| Semgrep | 0 findings |
| pip-audit | No known vulnerabilities |
| Safety | 0 vulnerabilities |
| Docker build | Pass |
| HTTPS smoke | Pass, app responds over HTTPS |
| Admin login smoke | Pass, valid admin login redirects to `/dashboard` |

## Control Verification

| Control | Evidence |
|---|---|
| Password hashes used | `generate_password_hash` and `check_password_hash` in `app/app.py` |
| Session cleared on login/logout | `session.clear()` in login and logout handlers |
| Admin-only routes protected | `@roles_required("admin")` on `/admin` |
| Member ownership enforced | `can_manage_project()` and task owner checks |
| Viewer write access blocked | Viewer cannot access create/edit/delete routes |
| SQL queries parameterized | `db.execute(..., params)` throughout auth, project, task, feedback, and admin routes |
| User content escaped | Jinja templates render variables normally; no `render_template_string()` path for user content |
| Dependencies checked | pip-audit and Safety clean in current scan |
| DAST executed | OWASP ZAP baseline configured in `.github/workflows/dast.yml` with `zap-scan-report` artifact |

## Residual Risk

The duplicate-registration response still confirms when a username or email already exists. This is accepted as a medium residual risk for the coursework demo because the message improves usability and the practical attack chain is reduced by rate limiting, stronger password rules, CSRF protection, hashed passwords, and RBAC. For production, the better pattern is a generic registration response plus email verification.

The current pipeline archives security findings for review instead of automatically failing all SAST/SCA/DAST jobs on severity. This is acceptable for an educational evidence workflow if the report clearly states the behavior and GitHub Issues track remediation. For production, the next improvement should be severity-based blocking gates on high-confidence critical/high findings.

## Final Sign-Off

| Role | Name | Date |
|---|---|---|
| Developer | Bilal Ahmed | 2026-05-12 |
| Security / Pipeline Reviewer | Ifrah Chishti | 2026-05-12 |
| Pentest / Retest Reviewer | Sabahatullah Shaikh | 2026-05-12 |
