# Remediation and Retest Report - NexusPortal

## Summary

Describe the issues fixed, the security controls added, and the retest outcome.

## Remediation Tracker

| Issue | Finding | Fix Summary | Commit | Retest Result |
|---|---|---|---|---|
| `#<id>` | `<finding>` | `<fix>` | `<hash>` | Pass/Fail |

## Retest Commands

```bash
python -m pytest tests -q
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

## Control Verification

| Control | Evidence |
|---|---|
| Password hashes used | `<screenshot/code reference>` |
| Session cleared on login/logout | `<test result/code reference>` |
| Admin-only routes protected | `<manual test/test case>` |
| Member ownership enforced | `<manual test/test case>` |
| Viewer write access blocked | `<manual test/test case>` |
| SQL queries parameterized | `<code reference/tool result>` |
| User content escaped | `<template/code reference>` |
| Dependencies checked | `<pip-audit/Safety artifact>` |
| DAST executed | `<ZAP artifact>` |

## Residual Risk

List accepted risks and future improvements, such as MFA, audit logging,
rate-limiting, CSRF protection, centralized logging, and production database
migration.

## Final Sign-Off

| Role | Name | Date |
|---|---|---|
| Developer | `<name>` | `<date>` |
| Tester | `<name>` | `<date>` |
| Reviewer | `<name>` | `<date>` |
