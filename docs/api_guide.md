# API Guide — BMAD v6 Template Architect

The BMAD v6 Architect is a server-side rendered (SSR) web application. All endpoints return HTML. There is no REST/JSON API. The routes below constitute the complete interface.

All routes except `GET /`, `GET /login`, `POST /login`, `GET /register`, and `POST /register` require authentication. Unauthenticated requests to protected routes receive a `302` redirect to `/login?next=<original_path>`.

---

## Routes

### `GET /login`

**View:** `templates/login.html`

Displays the username/password login form. Redirects to `/` if already authenticated.

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
| `302` | Redirect to `/` (or `next` param if a safe relative path) on success |
| `200` | Re-render login page with flash error on failure or suspended account |
| `403` | CSRF token missing or invalid |

---

### `GET /register`

**View:** `templates/register.html`

Displays the self-registration form. Redirects to `/` if already authenticated.

---

### `POST /register`

Creates a new user account (role defaults to `user`).

**Form Fields**

| Field | Required | Validation |
|---|---|---|
| `_csrf` | Yes | CSRF token |
| `full_name` | Yes | Non-empty string |
| `email` | Yes | Valid email format; must be unique |
| `username` | Yes | 3–50 chars; letters, digits, dots, hyphens, underscores |
| `contact_number` | Yes | 7–30 chars; digits, spaces, `+`, `-`, `(`, `)` |
| `password` | Yes | Minimum 8 characters |
| `confirm_password` | Yes | Must match `password` |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/login` on success |
| `200` | Re-render registration form with flash errors on validation failure |
| `403` | CSRF token missing or invalid |

---

### `GET /logout`

Logs out the current user and destroys the session.

**Requires:** Any authenticated role.

**Response:** `302` redirect to `/login`.

---

### `GET /change_password`

**View:** `templates/change_password.html`

Displays the change-password form.

**Requires:** Any authenticated role.

---

### `POST /change_password`

Updates the current user's password.

**Requires:** Any authenticated role.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |
| `current_password` | Yes | Existing password (verified against stored hash) |
| `new_password` | Yes | New password (minimum 8 characters) |
| `confirm_password` | Yes | Must match `new_password` |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/` on success |
| `200` | Re-render form with flash errors on validation failure |
| `403` | CSRF token missing or invalid |

---

### `GET /`

**View:** `templates/index.html`

Lists all available BMAD templates (agents and documents).

**Access:** All roles (including unauthenticated).

**Template Variables**

| Variable | Type | Description |
|---|---|---|
| `templates` | list of dict | Each entry has `id`, `name`, `is_agent`, `sections`, `groups` |
| `config` | dict | Application settings from `config.yaml` |
| `groups` | list of str | Configured group labels for the filter bar |

---

### `GET /guide/<template_id>`

**View:** `templates/guide.html`

Renders the step-by-step guided interview form for the specified template.

**Requires:** `admin`, `super_user`, or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `template_id` | int | Zero-based index of the template in `bmad_library.json` |

Returns `404` if `template_id` is out of range.

---

### `POST /guide/<template_id>`

Processes the submitted guided interview form and generates sharded BMAD v6 output.

**Requires:** `admin`, `super_user`, or `user` role.

**Form Fields**

| Field | Required | Max Length | Description |
|---|---|---|---|
| `_csrf` | Yes | 64 chars | CSRF token (injected by `{{ csrf_token() }}`) |
| `agent_name` | Yes | 100 chars | Output folder name (sanitised to filesystem-safe string) |
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

**Requires:** `admin`, `super_user`, or `user` role.

---

### `GET /success/<agent_name>`

**View:** `templates/success.html`

Displays the list of generated files for `agent_name`.

**Requires:** `admin`, `super_user`, or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `agent_name` | str | Name of the generated agent folder |

**File visibility by role:**

| Role | Files shown |
|---|---|
| `admin` | All files (shards + consolidated document) |
| `super_user`, `user` | Only `<agent_name>_complete.md` |

---

### `GET /download/<agent_name>`

Streams a ZIP archive of all sharded files inside `bmad_output/<agent_name>/`.

**Requires:** `admin` or `super_user` role.

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

### `GET /download_md/<agent_name>`

Streams the consolidated Markdown document (`<agent_name>_complete.md`) for a given agent.

**Requires:** `admin`, `super_user`, or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `agent_name` | str | Name of the generated agent folder |

**Response Headers**

```
Content-Type: text/markdown
Content-Disposition: attachment; filename="<agent_name>_complete.md"
```

Returns `404` if the folder or file does not exist.
Returns `403` if the resolved path escapes the output directory (path-traversal guard).

---

### `POST /delete/<agent_name>`

Permanently deletes a generated agent/document directory from `bmad_output/`.

**Requires:** `admin` or `super_user` role.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/dashboard` on success |
| `403` | CSRF token invalid, or path-traversal guard triggered |
| `404` | Agent folder not found |

---

### `GET /view_file/<agent_name>/<filename>`

Serves an individual Markdown file for in-browser viewing.

**Requires:** `admin`, `super_user`, or `user` role.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `agent_name` | str | Name of the generated agent folder |
| `filename` | str | Markdown filename (must end with `.md`) |

**Access restrictions:**

- Non-admin users may only view `<agent_name>_complete.md`. Attempts to view shard files return `403`.
- File must exist and be inside the agent directory (double path-traversal guard).

**Response:** `text/plain; charset=utf-8`

Returns `403` if the file extension is not `.md`, if the user's role does not permit access, or if path-traversal is detected.
Returns `404` if the file does not exist.

---

### `GET /amend/<template_id>`

**View:** `templates/amend.html`

Renders a form to update the default section content and group assignments for a template.

**Requires:** `admin` role.

---

### `POST /amend/<template_id>`

Saves updated default section content and groups back to `config/bmad_library.json`.

**Requires:** `admin` role.

**Form Fields**

| Field | Required | Max Length | Description |
|---|---|---|---|
| `_csrf` | Yes | 64 chars | CSRF token |
| `groups` | No | — | Zero or more selected group names (must be from configured groups list) |
| `<section_key>` | No | 8,192 chars | New default text for each section |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/` on success |
| `403` | CSRF token missing or invalid |
| `404` | Template not found |

---

### `GET /import`

**View:** `templates/import.html`

Renders the template import form.

**Requires:** `admin` role.

---

### `POST /import`

Imports a BMAD v6 template from an uploaded Markdown (`.md`) file.

**Requires:** `admin` role.

**Form Fields** (`enctype="multipart/form-data"`)

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |
| `md_file` | Yes | Markdown file to import (`.md` extension; max 500 KB; UTF-8 encoded) |
| `groups` | No | Zero or more group names to assign (overrides frontmatter groups) |
| `is_agent` | No | `"true"` or `"false"` radio (overrides frontmatter `is_agent`) |

**Responses**

| Status | Meaning |
|---|---|
| `302` | Redirect to `/` on success |
| `200` | Re-render import form with flash warning on validation failure |
| `403` | CSRF token missing or invalid |

---

## Admin — User Management Routes

All routes below require `admin` role. All POST routes require a valid `_csrf` token.

### `GET /admin/users`

**View:** `templates/admin_users.html`

Lists all registered user accounts with management actions.

---

### `POST /admin/users/<username>/suspend`

Toggles the `suspended` status of a user account.

An administrator cannot suspend their own account.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |

**Responses:** `302` redirect to `/admin/users`.

---

### `POST /admin/users/<username>/delete`

Permanently deletes a user account from `config/users.yaml`.

An administrator cannot delete their own account.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |

**Responses:** `302` redirect to `/admin/users`. Returns `404` if user not found.

---

### `POST /admin/users/<username>/role`

Changes the role of a user account.

An administrator cannot change their own role.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |
| `role` | Yes | New role — one of `user`, `super_user`, `admin` |

**Responses:** `302` redirect to `/admin/users`. Returns `404` if user not found.

---

### `POST /admin/users/<username>/set_password`

Sets any user's password without requiring the current password.

**Form Fields**

| Field | Required | Description |
|---|---|---|
| `_csrf` | Yes | CSRF token |
| `new_password` | Yes | New password (minimum 8 characters) |
| `confirm_password` | Yes | Must match `new_password` |

**Responses:** `302` redirect to `/admin/users`. Returns `404` if user not found.

---

## Error Handlers

| HTTP Status | Trigger | View |
|---|---|---|
| `403 Forbidden` | CSRF failure, role check failure, path-traversal detection | `templates/error.html` |
| `404 Not Found` | Missing template ID, agent folder, or file | `templates/error.html` |
| `500 Internal Server Error` | Unhandled application exception | `templates/error.html` |

---

## Security Headers on All Responses

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self';` |
| `Server` | *(removed — no fingerprinting)* |
