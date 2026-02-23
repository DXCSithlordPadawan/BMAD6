# API Guide — BMAD v6 Template Architect

The BMAD v6 Architect is a server-side rendered (SSR) web application. All endpoints return HTML. There is no REST/JSON API. The routes below constitute the full interface.

All routes except `GET /`, `GET /login`, and `POST /login` require authentication. Unauthenticated requests to protected routes receive a `302` redirect to `/login?next=<original_path>`.

---

## Routes

### `GET /login`

**View:** `templates/login.html`

Displays the username/password login form.

---

### `POST /login`

Authenticates the user and creates a session.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |
| `username` | Yes | Username (max 100 chars) |
| `password` | Yes | Password |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/` (or `next` param) on success |
| `200` | Re-render login page with flash error on failure |
| `403` | CSRF token missing or invalid |

---

### `GET /logout`

Logs out the current user and destroys the session.

**Requires:** Any authenticated role.

**Response:** `302` redirect to `/login`.

---

### `GET /`

**View:** `templates/index.html`

Lists all available BMAD templates (agents and documents).

**Access:** All roles (including unauthenticated).

**Template Variables**

| Variable | Type | Description |
|---|---|---|
| `templates` | list of dict | Each entry has `id`, `name`, `is_agent`, `sections` |
| `config` | dict | Application settings from `config.yaml` |

---

### `GET /guide/<template_id>`

**View:** `templates/guide.html`

Renders the step-by-step guided interview form for the specified template.

**Requires:** `admin` or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `template_id` | int | Zero-based index of the template in `bmad_library.json` |

Returns `404` if `template_id` is out of range.

---

### `POST /guide/<template_id>`

Processes the submitted guided interview form and generates sharded BMAD v6 output.

**Requires:** `admin` or `user` role.

**Form Fields**

| Field | Required | Max Length | Description |
|---|---|---|---|
| `_csrf` | Yes | 64 chars | CSRF token (injected by `{{ csrf_token() }}`) |
| `agent_name` | Yes | 100 chars | Output folder name |
| `<section_key>` | No | 8,192 chars | One field per template section |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/success/<agent_name>` on success |
| `403` | CSRF token missing or invalid |
| `404` | Template not found |

---

### `GET /dashboard`

**View:** `templates/dashboard.html`

Shows a list of all agent directories in `bmad_output/`.

**Requires:** `admin`, `user`, or `security_lead` role.

---

### `GET /success/<agent_name>`

**View:** `templates/success.html`

Displays the list of generated files for `agent_name`.

**Requires:** `admin` or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `agent_name` | str | Name of the generated agent folder |

---

### `GET /download/<agent_name>`

Streams a ZIP archive of all files inside `bmad_output/<agent_name>/`.

**Requires:** `admin` or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `agent_name` | str | Name of the generated agent folder |

**Response Headers**

```
Content-Type: application/zip
Content-Disposition: attachment; filename="<agent_name>.zip"
```

Returns `404` if the folder does not exist.
Returns `403` if the resolved path escapes the output directory (path-traversal guard).

---

### `GET /amend/<template_id>`

**View:** `templates/amend.html`

Renders a form to update the default section content for a template.

**Requires:** `admin` or `user` role.

---

### `POST /amend/<template_id>`

Saves updated default section content back to `config/bmad_library.json`.

**Requires:** `admin` or `user` role.

**Form Fields**

| Field | Required | Max Length | Description |
|---|---|---|---|
| `_csrf` | Yes | 64 chars | CSRF token |
| `<section_key>` | No | 8,192 chars | New default text for each section |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/` on success |
| `403` | CSRF token missing or invalid |
| `404` | Template not found |

---

## Security Headers on All Responses

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'none';` |

