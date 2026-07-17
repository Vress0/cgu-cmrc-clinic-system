# Security Notes

## Authentication And RBAC

- Access tokens are short lived.
- Refresh tokens rotate.
- Passwords are stored with Argon2.
- Backend permissions are enforced through RBAC dependencies.
- Admin-only endpoints include user management and audit logs.

## Default Admin

Development defaults:

```text
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=ChangeMe123!
```

Before production:

- Replace `SECRET_KEY`.
- Replace `DEFAULT_ADMIN_PASSWORD`.
- Create named administrator accounts.
- Disable or rotate the bootstrap admin after handoff.
- Track first-login password change as a required follow-up; the current schema does not yet enforce it.

## Nginx Headers

The Nginx config sets:

- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Permissions-Policy`
- `Content-Security-Policy`

Add `Strict-Transport-Security` only after HTTPS is configured.

## Audit Results

Python:

- `uvx pip-audit`
- Result during Phase 4 finalization: no known vulnerabilities found.

Frontend:

- `npm audit --audit-level=moderate`
- Result during Phase 4 finalization: 2 moderate vulnerabilities through Next.js' PostCSS dependency path.
- Advisory: PostCSS CSS stringify output XSS advisory.
- The suggested `npm audit fix --force` would install a breaking Next.js version path, so it was not applied automatically.
- Mitigation: monitor Next.js patch releases and upgrade through a normal dependency update branch with full frontend build and browser smoke testing.

## Public Port Policy

Production should expose only Nginx on `80/443`. Do not expose PostgreSQL, backend, or frontend service ports directly.
