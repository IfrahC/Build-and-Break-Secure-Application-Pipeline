# Weekly Plan - NexusPortal Build and Break

## Week 1 - Design and Threat Model

1. Run the app locally with Docker.
2. Walk through all roles:
   - Admin: `admin@nexus.local` / `Admin1234`
   - Member: `member@nexus.local` / `Member1234`
   - Viewer: `viewer@nexus.local` / `Viewer1234`
3. Map the attack surface:
   - Public auth routes
   - Session-protected routes
   - Admin-only role management
   - Project/task CRUD
   - Feedback form
   - SQLite database
   - Docker container boundary
4. Complete `docs/threat-model-template.md`.
5. Create GitHub Issues for key threats and planned fixes.

Suggested threat examples:

| Area | Threat |
|---|---|
| Authentication | Brute force, weak password registration, session fixation |
| Authorization | Member accesses another member project, viewer performs writes |
| Injection | SQL injection in login/search/forms |
| XSS | Feedback or project text rendered unsafely |
| Data exposure | Admin-only data visible to non-admin users |
| Dependencies | Known vulnerable Python packages |
| Container | App running as root, debug mode enabled |

## Week 2 - Build, Test, SAST, SCA

1. Confirm core app features work:
   - Login/logout
   - Register
   - Project CRUD
   - Task create/update/delete
   - Search/filter
   - Feedback submit/review
   - Admin role changes
2. Run tests:

```bash
python -m pytest tests -q
```

3. Run SAST:

```bash
bandit -r app/
semgrep --config=auto \
  --exclude-rule python.django.security.django-no-csrf-token.django-no-csrf-token \
  app/
```

4. Run SCA:

```bash
pip-audit -r app/requirements.txt
safety check -r app/requirements.txt
```

5. Open GitHub Issues for findings and reference them in commits.

## Week 3 - DAST and Manual Testing

1. Start the Dockerized app:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

2. Run OWASP ZAP baseline:

```bash
docker run --rm -t ghcr.io/zaproxy/zaproxy \
  zap-baseline.py -t http://host.docker.internal:5000
```

3. Manually test business logic:
   - Viewer cannot access create/edit/delete routes.
   - Member cannot open or mutate projects owned by another user.
   - Admin can update roles, but at least one admin remains.
   - Invalid project/task/feedback inputs are rejected.
   - Login uses parameterized queries and rejects SQLi payloads.
   - User-provided content is escaped in HTML.

4. Document evidence in `docs/exploitation-report-template.md`.

## Week 4 - Remediation, Retest, Report

1. Fix confirmed issues.
2. Retest with pytest, SAST, SCA, and DAST.
3. Complete:
   - `docs/remediation-report-template.md`
   - `docs/executive-summary-template.md`
4. Prepare a live demo:
   - Show the app by role.
   - Show GitHub Issues and linked commits.
   - Show Actions artifacts for SAST/SCA/DAST/coverage.
   - Explain one business logic flaw and its fix.

## Commit Format

Reference GitHub Issues in commits:

```bash
git commit -m "Refs #12: add project ownership tests"
git commit -m "Fixes #13: block viewer project mutation"
```
