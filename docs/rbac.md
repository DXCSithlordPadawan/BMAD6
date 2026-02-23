# RBAC Document — BMAD v6 Template Architect

## 1. Overview

The BMAD v6 Architect implements **in-application authentication and role-based access control (RBAC)** using Flask-Login and HMAC-backed CSRF protection.

All users must log in with a username and password before accessing protected routes. Accounts and roles are defined in `config/users.yaml`. Password hashes use Werkzeug's `generate_password_hash` (scrypt by default on Python 3.12+, argon2/pbkdf2 on older systems).

---

## 2. Defined Roles

| Role | Description | Access Level |
|---|---|---|
| **Anonymous / Unauthenticated** | Any user who has not logged in | Read-only: view template list (`GET /`) and login page |
| **`user`** | A standard authenticated user | Guide, generate, download, dashboard, amend |
| **`admin`** | Administrator — full in-application access | All routes including amend/edit |
| **`security_lead`** | Security auditor | Dashboard and template list only |
| **`devops`** | Infrastructure operator | Template list (read) only; no write routes |

---

## 3. RBAC Matrix

| Action | Anonymous | `user` | `admin` | `devops` | `security_lead` |
|---|:---:|:---:|:---:|:---:|:---:|
| View template list (`GET /`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Login (`GET/POST /login`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Use guided interview (`GET/POST /guide/<id>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| View success page (`GET /success/<name>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| View dashboard (`GET /dashboard`) | ❌ | ✅ | ✅ | ❌ | ✅ |
| Download ZIP (`GET /download/<name>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| Amend template defaults (`GET/POST /amend/<id>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| Edit `config.yaml` (filesystem) | ❌ | ❌ | ✅ | ✅ | ❌ |
| Edit `config/users.yaml` (filesystem) | ❌ | ❌ | ✅ | ✅ | ❌ |
| Rotate `SECRET_KEY` | ❌ | ❌ | ✅ | ✅ | ✅ |
| Access application logs | ❌ | ❌ | ✅ | ✅ | ✅ |
| Rebuild and redeploy container | ❌ | ❌ | ❌ | ✅ | ❌ |

> **Note:** Route-level enforcement is performed by the `@login_required` and `@role_required(...)` decorators in `app.py`. Infrastructure-level actions (config editing, log access, container deployment) remain the responsibility of the host OS and container platform.

---

## 4. User Management

### User accounts file: `config/users.yaml`

```yaml
users:
  - username: admin
    password_hash: "<werkzeug hash>"
    role: admin
  - username: analyst
    password_hash: "<werkzeug hash>"
    role: user
  - username: auditor
    password_hash: "<werkzeug hash>"
    role: security_lead
```

### Generating a password hash

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_secure_password'))"
```

Paste the output into `password_hash` for the relevant user entry.

### Adding a new user

1. Generate a password hash as above.
2. Add a new entry to `config/users.yaml`.
3. Restart the application (the users file is reloaded on each request).

### Changing a password

1. Generate a new hash.
2. Replace the existing `password_hash` value in `config/users.yaml`.
3. No restart required (users are loaded per-request).

### Removing a user

Delete the relevant entry from `config/users.yaml`.

> **Security:** Always change the default `admin` password (`changeme`) before deploying to any non-development environment.

---

## 5. Authentication Flow

```
Browser → GET /protected-route
         ← 302 /login?next=/protected-route

Browser → POST /login (username, password, _csrf)
         ← 302 /protected-route  (on success)
         ← 200 /login            (on failure, with flash message)

Browser → GET /logout
         ← 302 /login
```

---

## 6. Implementing Additional Network-Layer Controls

For defence in depth, consider also applying network-layer controls:

### nginx example (`/etc/nginx/conf.d/bmad.conf`)

```nginx
server {
    listen 443 ssl;
    server_name bmad.internal.example.com;

    # Restrict to internal network range
    allow 10.0.0.0/8;
    deny all;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Alternative: require VPN / Tailscale

Deploy the application on a host accessible only via VPN. This provides a second authentication layer on top of the in-application login.

---

## 7. Future Enhancements

If enterprise SSO is required:

- **LDAP / Active Directory** via `flask-ldap3-login`
- **OAuth2 / OIDC** (e.g., Keycloak, Azure AD) via `Authlib`
- Database-backed per-user output directories for multi-tenant use
