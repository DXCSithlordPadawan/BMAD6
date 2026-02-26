# RBAC Document — BMAD v6 Template Architect

## 1. Overview

The BMAD v6 Architect implements **in-application authentication and role-based access control (RBAC)** using Flask-Login and HMAC-backed CSRF protection.

All users must log in with a username and password before accessing protected routes. Accounts and roles are defined in `config/users.yaml`. Password hashes use Werkzeug's `generate_password_hash` (scrypt by default on Python 3.12+, argon2/pbkdf2 on older systems).

New users may self-register at `/register`. All self-registered accounts default to the **`user`** role. An administrator can subsequently promote a user by editing `config/users.yaml` and setting their `role` to `super_user` or `admin`.

---

## 2. Defined Roles

| Role | Description | Access Level |
|---|---|---|
| **Anonymous / Unauthenticated** | Any user who has not logged in | View template list (`GET /`) and login/register pages only |
| **`user`** | Standard authenticated user | Guide interview, generate documents, view dashboard, download Consolidated Markdown |
| **`super_user`** | Elevated user | All `user` permissions plus: delete generated documents, download ZIP archives |
| **`admin`** | Administrator — full in-application access | All `super_user` permissions plus: amend/edit template defaults, import templates, manage users (suspend/delete) |

---

## 3. RBAC Matrix

| Action | Anonymous | `user` | `super_user` | `admin` |
|---|:---:|:---:|:---:|:---:|
| View template list (`GET /`) | ✅ | ✅ | ✅ | ✅ |
| Login (`GET/POST /login`) | ✅ | ✅ | ✅ | ✅ |
| Register (`GET/POST /register`) | ✅ | ✅ | ✅ | ✅ |
| Use guided interview (`GET/POST /guide/<id>`) | ❌ | ✅ | ✅ | ✅ |
| View success page (`GET /success/<name>`) | ❌ | ✅ | ✅ | ✅ |
| View dashboard (`GET /dashboard`) | ❌ | ✅ | ✅ | ✅ |
| Download Consolidated Markdown (`GET /download_md/<name>`) | ❌ | ✅ | ✅ | ✅ |
| **Change own password (`GET/POST /change_password`)** | ❌ | ✅ | ✅ | ✅ |
| Download ZIP (`GET /download/<name>`) | ❌ | ❌ | ✅ | ✅ |
| Delete generated document (`POST /delete/<name>`) | ❌ | ❌ | ✅ | ✅ |
| Amend template defaults (`GET/POST /amend/<id>`) | ❌ | ❌ | ❌ | ✅ |
| Import template (`GET/POST /import`) | ❌ | ❌ | ❌ | ✅ |
| Manage users (`GET /admin/users`) | ❌ | ❌ | ❌ | ✅ |
| Suspend/unsuspend user (`POST /admin/users/<u>/suspend`) | ❌ | ❌ | ❌ | ✅ |
| Delete user (`POST /admin/users/<u>/delete`) | ❌ | ❌ | ❌ | ✅ |
| Change user role (`POST /admin/users/<u>/role`) | ❌ | ❌ | ❌ | ✅ |
| **Set any user's password (`POST /admin/users/<u>/set_password`)** | ❌ | ❌ | ❌ | ✅ |
| Edit `config.yaml` (filesystem) | ❌ | ❌ | ❌ | ✅ |
| Edit `config/users.yaml` (filesystem) | ❌ | ❌ | ❌ | ✅ |

> **Note:** Route-level enforcement is performed by the `@login_required` and `@role_required(...)` decorators in `app.py`. Infrastructure-level actions (config editing, log access, container deployment) remain the responsibility of the host OS and container platform.

---

## 4. User Registration

Users may self-register at `/register`. The registration form requires:

| Field | Requirement |
|---|---|
| **Full Name** | Required |
| **Email Address** | Required; must be a valid email format; must be unique |
| **Login Name (Username)** | Required; 3–50 chars; letters, digits, dots, hyphens, underscores |
| **Contact Number** | Required; 7–30 chars; digits, spaces, `+`, `-`, `(`, `)` |
| **Password** | Required; minimum 8 characters |
| **Confirm Password** | Must match Password |

All self-registered accounts default to the **`user`** role. An administrator must manually edit `config/users.yaml` to assign `super_user` or `admin` roles.

---

## 5. User Management (Admin)

Administrators may manage user accounts at `/admin/users`:

- **Suspend / Unsuspend** — Prevents (or re-enables) a user from logging in without deleting their account.
- **Delete** — Permanently removes the user from `config/users.yaml`.
- **Change Role** — Promotes or demotes a user between `user`, `super_user`, and `admin` roles.
- **Set Password** — Sets any user's password directly, without requiring the current password.

An administrator cannot suspend or delete their own account.

---

## 6. User Management via `config/users.yaml`

### User accounts file: `config/users.yaml`

```yaml
users:
  - username: admin
    password_hash: "<werkzeug hash>"
    role: admin
    full_name: "Administrator"
    email: "admin@example.com"
    contact_number: "+000000000"
    suspended: false
  - username: analyst
    password_hash: "<werkzeug hash>"
    role: user
    full_name: "Jane Analyst"
    email: "jane@example.com"
    contact_number: "+441234567890"
    suspended: false
```

### Generating a password hash

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_secure_password'))"
```

Paste the output into `password_hash` for the relevant user entry.

### Manually adding a user

1. Generate a password hash as above.
2. Add a new entry to `config/users.yaml` with all required fields.
3. Restart the application (the users file is reloaded on each request).

### Changing a password

**Via the UI (recommended):**

Any authenticated user can change their own password at `/change_password` (navigation bar **🔑 Change Password** link). Administrators can set any user's password from the `/admin/users` page.

**Via `config/users.yaml`:**

1. Generate a new hash.
2. Replace the existing `password_hash` value in `config/users.yaml`.
3. No restart required (users are loaded per-request).

### Removing a user

Delete the relevant entry from `config/users.yaml` or use the admin UI at `/admin/users`.

> **Security:** Always change the default `admin` password (`changeme`) before deploying to any non-development environment.

---

## 7. Authentication Flow

```
Browser → GET /protected-route
         ← 302 /login?next=/protected-route

Browser → POST /login (username, password, _csrf)
         ← 302 /protected-route  (on success, if account is active)
         ← 200 /login            (on failure or if account is suspended)

Browser → GET /register
Browser → POST /register (full_name, email, username, contact_number, password, confirm_password, _csrf)
         ← 302 /login            (on success)
         ← 200 /register         (on validation failure)

Browser → GET /change_password   (authenticated users only)
Browser → POST /change_password (current_password, new_password, confirm_password, _csrf)
         ← 302 /                 (on success)
         ← 200 /change_password  (on validation failure)

Browser → POST /admin/users/<u>/set_password (new_password, confirm_password, _csrf)  [admin only]
         ← 302 /admin/users      (on success or validation failure with flash message)

Browser → GET /logout
         ← 302 /login
```

---

## 8. Implementing Additional Network-Layer Controls

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

## 9. Future Enhancements

If enterprise SSO is required:

- **LDAP / Active Directory** via `flask-ldap3-login`
- **OAuth2 / OIDC** (e.g., Keycloak, Azure AD) via `Authlib`
- Database-backed per-user output directories for multi-tenant use
- Admin-approval workflow for newly registered accounts
