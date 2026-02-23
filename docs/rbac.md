# RBAC Document — BMAD v6 Template Architect

## 1. Overview

The BMAD v6 Architect is a **single-tenant, single-user** web application intended to be run locally or behind an authenticated reverse proxy. It does not currently implement in-application authentication or authorisation.

All access control is enforced at the **network / infrastructure layer** (see Deployment Guide).

---

## 2. Defined Roles

| Role | Description | Access Level |
|---|---|---|
| **Anonymous / Unauthenticated** | Any user who reaches the application without a valid session | Read-only: view template list |
| **Authenticated User** | A user who has been authenticated by the reverse proxy or VPN | Full use: guide, generate, download, amend |
| **Administrator** | Has shell / filesystem access to the deployment host | Full: manage config, restart service, rotate secrets |
| **DevOps** | Has container registry and Podman access | Deploy, rollback, monitor container |
| **Security Lead** | Reviews security posture | Audit logs, approve config changes |

---

## 3. RBAC Matrix

| Action | Anonymous | Authenticated User | Administrator | DevOps | Security Lead |
|---|:---:|:---:|:---:|:---:|:---:|
| View template list (`GET /`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Use guided interview (`GET/POST /guide/<id>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| View dashboard (`GET /dashboard`) | ❌ | ✅ | ✅ | ❌ | ✅ |
| Download ZIP (`GET /download/<name>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| Amend template defaults (`GET/POST /amend/<id>`) | ❌ | ✅ | ✅ | ❌ | ❌ |
| Edit `config.yaml` | ❌ | ❌ | ✅ | ✅ | ❌ |
| Rotate `SECRET_KEY` | ❌ | ❌ | ✅ | ✅ | ✅ |
| Access application logs | ❌ | ❌ | ✅ | ✅ | ✅ |
| Rebuild and redeploy container | ❌ | ❌ | ❌ | ✅ | ❌ |

> **Note:** The application itself does not enforce the "Anonymous" vs "Authenticated User" distinction. This MUST be implemented at the reverse proxy layer (e.g., nginx `auth_basic`, Traefik forward auth, or VPN requirement).

---

## 4. Implementing Access Control at the Proxy Layer

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

Deploy the application on a host accessible only via VPN. This satisfies the "Authenticated User" requirement at the network level.

---

## 5. Future Enhancements

If multi-user support is required in a future version, consider integrating:

- **Flask-Login** for session-based authentication
- **LDAP / Active Directory** via `flask-ldap3-login`
- **OAuth2 / OIDC** (e.g., Keycloak, Azure AD) via `Authlib`
- Database-backed per-user output directories
