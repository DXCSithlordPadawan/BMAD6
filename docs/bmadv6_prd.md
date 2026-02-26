# Product Requirements Document — BMAD v6 Template Architect

**Document version:** 1.0  
**Application name:** DXC Agile Innovation Program BMAD Forge V6 (Build More Architect Dreams)  
**Short name:** BMAD v6 Template Architect  
**Repository:** `DXCSithlordPadawan/BMAD6`

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Technology Stack](#2-technology-stack)
3. [Repository Structure](#3-repository-structure)
4. [Configuration Files](#4-configuration-files)
5. [Authentication and RBAC](#5-authentication-and-rbac)
6. [Application Entry Point — app.py](#6-application-entry-point--apppy)
7. [Routes and Business Logic](#7-routes-and-business-logic)
8. [BMAD v6 Sharding Engine](#8-bmad-v6-sharding-engine)
9. [Template Library](#9-template-library)
10. [HTML Templates (Jinja2)](#10-html-templates-jinja2)
11. [Static Assets](#11-static-assets)
12. [Security Architecture](#12-security-architecture)
13. [Containerisation](#13-containerisation)
14. [Environment Variables](#14-environment-variables)
15. [Deployment](#15-deployment)
16. [Non-Functional Requirements](#16-non-functional-requirements)
17. [Complete File Inventory](#17-complete-file-inventory)

---

## 1. Purpose and Scope

### 1.1 What the Application Does

The BMAD v6 Template Architect is a **Python Flask web application** that guides users through a structured, step-by-step interview process. The output is a folder of **sharded Markdown files** that are BMAD v6-compliant and ready for submission to any AI model.

Instead of one large Markdown file, the tool produces a **sharded folder** containing:

| File | Purpose |
|---|---|
| `agent.md` | Master controller — table of contents with a checklist of all shards |
| `step-00_<section>.md` | First section shard |
| `step-01_<section>.md` | Second section shard |
| `step-NN_<section>.md` | Additional numbered section shards |
| `<agent_name>_complete.md` | Amalgamated single-file document (all sections concatenated) |

Each shard can be submitted to an AI model independently, reducing token usage while keeping context precise.

### 1.2 Core User Journey

1. User navigates to the home page (`/`) and sees a filterable grid of available templates.
2. User clicks **▶ Start Guide** on a template card.
3. (If not logged in, user is redirected to `/login`, then back to the guide.)
4. User fills in the step-by-step interview form — one textarea per template section, pre-populated with default text.
5. User submits the form and receives a **success page** showing the generated files.
6. User downloads either the consolidated single Markdown file or a ZIP of all shards.

### 1.3 Primary User Personas

| Persona | Role | Key Need |
|---|---|---|
| AI Author | `user` | Fill in templates, download Markdown for AI submission |
| Power User | `super_user` | All user capabilities, plus delete documents and download ZIPs |
| Administrator | `admin` | Full control including user management and template editing |

---

## 2. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.12+ |
| Web Framework | Flask | ≥3.0.0 |
| Authentication | Flask-Login | ≥0.6.3 |
| Templating | Jinja2 | bundled with Flask |
| Config Parsing | PyYAML | ≥6.0.1 |
| Environment Management | python-dotenv | ≥1.0.0 |
| HTML Sanitisation | MarkupSafe | ≥2.1.5 |
| Password Hashing | Werkzeug | ≥3.0.0 |
| Containerisation | Podman / Docker | compatible |
| Container Base Image | python:3.12-slim | official |

### 2.1 requirements.txt

```
Flask>=3.0.0
Flask-Login>=0.6.3
PyYAML>=6.0.1
python-dotenv>=1.0.0
MarkupSafe>=2.1.5
Werkzeug>=3.0.0
```

### 2.2 Python Standard Library Modules Used

`functools`, `hmac`, `io`, `json`, `logging`, `os`, `re`, `secrets`, `shutil`, `zipfile`, `pathlib.Path`

---

## 3. Repository Structure

```
BMAD6/
├── app.py                     # Flask application (single file — all routes and logic)
├── requirements.txt           # Python dependencies
├── Containerfile              # Podman / Docker multi-stage build
├── .env.example               # Environment variable template
├── .gitignore                 # Excludes bmad_output/, venv/, __pycache__/, .env
│
├── config/
│   ├── config.yaml            # Application settings
│   ├── users.yaml             # User accounts (usernames, hashed passwords, roles)
│   └── bmad_library.json      # Template library (all agent and document templates)
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base layout (nav bar, flash messages, footer)
│   ├── index.html             # Template list with group filter
│   ├── login.html             # Login form
│   ├── register.html          # Self-registration form
│   ├── change_password.html   # Change own password form
│   ├── guide.html             # Step-by-step interview form
│   ├── dashboard.html         # List of all generated agents/documents
│   ├── success.html           # Post-generation confirmation
│   ├── amend.html             # Edit template default sections (admin)
│   ├── import.html            # Import template from .md file (admin)
│   ├── admin_users.html       # User management table (admin)
│   └── error.html             # Generic error page (403/404/500)
│
├── static/
│   ├── css/
│   │   └── dashboard.css      # Dark-mode stylesheet for all pages
│   └── js/
│       └── filter.js          # Client-side group filter logic (index page)
│
├── agent/
│   └── agent.md.j2            # Reference Jinja2 agent template (illustrative only)
│
├── bmad_output/               # Generated agents/documents (gitignored; created at runtime)
│   └── <agent_name>/
│       ├── agent.md
│       ├── step-00_*.md
│       ├── step-NN_*.md
│       └── <agent_name>_complete.md
│
├── docs/                      # Project documentation
│   ├── architecture.md
│   ├── user_guide.md
│   ├── api_guide.md
│   ├── support_tasks.md
│   ├── raci.md
│   ├── rbac.md
│   ├── security.md
│   ├── maintenance.md
│   ├── deployment.md
│   ├── container_build.md
│   └── bmadv6_prd.md          # ← this document
│
├── python/                    # Legacy Django code fragments (reference only — not executed)
├── html/                      # Legacy HTML fragments (reference only — not executed)
└── scripts/
    └── import_bmad_library.sh # Utility shell script
```

---

## 4. Configuration Files

### 4.1 `config/config.yaml`

```yaml
app_settings:
  application_title: "DXC Agile Innovation Program BMAD Forge V6 (Build More Architect Dreams)"
  web_port: 8000
  base_location: "./bmad_output/"
  icon: "👩‍💻"
  sharding_enabled: true
  groups:
    - Discovery
    - Phase 1
    - Phase 2
    - Phase 3
    - Phase 4
    - Planning
    - Development
    - Deployment
    - QA
    - Testing
    - Integration
    - Agents
    - Documents
```

| Key | Type | Description |
|---|---|---|
| `application_title` | string | Shown in the nav bar and in generated Markdown headers |
| `web_port` | integer | TCP port the Flask development server listens on (default: 8000) |
| `base_location` | string | Relative path where generated agent folders are written |
| `icon` | string | Emoji displayed next to the application title throughout the UI |
| `sharding_enabled` | boolean | Reserved for future use; always `true` |
| `groups` | list of strings | Amendable list of functional group labels for template categorisation |

### 4.2 `config/users.yaml`

```yaml
users:
  - username: admin
    password_hash: "<werkzeug scrypt hash>"
    role: admin
    full_name: "Administrator"
    email: "admin@example.com"
    contact_number: "+000000000"
    suspended: false
```

Each user entry has these exact fields:

| Field | Type | Description |
|---|---|---|
| `username` | string | Login name; also used as Flask-Login user ID |
| `password_hash` | string | Werkzeug `generate_password_hash` output (scrypt on Python 3.12+) |
| `role` | string | One of `user`, `super_user`, `admin` |
| `full_name` | string | Display name |
| `email` | string | Must be unique across all users |
| `contact_number` | string | Phone number |
| `suspended` | boolean | When `true` the user cannot log in |

The default admin account uses the password `changeme` — this must be changed before any deployment.

### 4.3 `config/bmad_library.json`

JSON array of template objects. Each object:

```json
{
  "name": "Template Name",
  "is_agent": true,
  "groups": ["Planning", "Development"],
  "sections": {
    "persona": "Default persona text…",
    "workflow": "Default workflow text…",
    "constraints": "Default constraints text…"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `name` | string | Display name and also the default output folder name |
| `is_agent` | boolean | `true` = Agent template; `false` = Document template |
| `groups` | list of strings | Subset of groups defined in `config.yaml` |
| `sections` | object | Ordered key→value pairs where the key is a snake_case section name and the value is the default textarea content |

The application injects an `id` field (zero-based index) at runtime — this field must **not** be persisted back to the JSON file.

### 4.4 `.env.example`

```
SECRET_KEY=replace_me_with_a_random_64_char_hex_string
FLASK_DEBUG=0
HTTPS_ENABLED=0
# SSL_CERT_FILE=/etc/ssl/certs/bmad.crt
# SSL_KEY_FILE=/etc/ssl/private/bmad.key
```

---

## 5. Authentication and RBAC

### 5.1 Roles

| Role | Description |
|---|---|
| `user` | Standard authenticated user |
| `super_user` | Elevated user |
| `admin` | Full administrator access |

### 5.2 RBAC Matrix

| Action / Route | Unauthenticated | `user` | `super_user` | `admin` |
|---|:---:|:---:|:---:|:---:|
| `GET /` (template list) | ✅ | ✅ | ✅ | ✅ |
| `GET/POST /login` | ✅ | ✅ | ✅ | ✅ |
| `GET/POST /register` | ✅ | ✅ | ✅ | ✅ |
| `GET/POST /guide/<id>` | ❌ | ✅ | ✅ | ✅ |
| `GET /success/<name>` | ❌ | ✅ | ✅ | ✅ |
| `GET /dashboard` | ❌ | ✅ | ✅ | ✅ |
| `GET /download_md/<name>` | ❌ | ✅ | ✅ | ✅ |
| `GET /view_file/<name>/<name>_complete.md` | ❌ | ✅ | ✅ | ✅ |
| `GET/POST /change_password` | ❌ | ✅ | ✅ | ✅ |
| `GET /download/<name>` (ZIP) | ❌ | ❌ | ✅ | ✅ |
| `POST /delete/<name>` | ❌ | ❌ | ✅ | ✅ |
| `GET /view_file/<name>/<shard>.md` (non-complete shards) | ❌ | ❌ | ❌ | ✅ |
| `GET/POST /amend/<id>` | ❌ | ❌ | ❌ | ✅ |
| `GET/POST /import` | ❌ | ❌ | ❌ | ✅ |
| `GET /admin/users` | ❌ | ❌ | ❌ | ✅ |
| `POST /admin/users/<u>/suspend` | ❌ | ❌ | ❌ | ✅ |
| `POST /admin/users/<u>/delete` | ❌ | ❌ | ❌ | ✅ |
| `POST /admin/users/<u>/role` | ❌ | ❌ | ❌ | ✅ |
| `POST /admin/users/<u>/set_password` | ❌ | ❌ | ❌ | ✅ |
| `GET /logout` | ❌ | ✅ | ✅ | ✅ |

### 5.3 `ROLE_PERMISSIONS` Constant

The in-code mapping used by `@role_required`:

```python
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "index", "guide", "dashboard", "success",
        "download_zip", "download_md", "view_md_file",
        "amend_template", "delete_agent", "import_template",
        "admin_users", "suspend_user", "delete_user", "change_user_role",
        "admin_set_password", "change_password",
    },
    "super_user": {
        "index", "guide", "dashboard", "success",
        "download_zip", "download_md", "delete_agent", "view_md_file",
        "change_password",
    },
    "user": {
        "index", "guide", "dashboard", "success", "download_md", "view_md_file",
        "change_password",
    },
}
```

### 5.4 User Registration Validation

Self-registration at `/register` enforces:

| Field | Validation Rule |
|---|---|
| `full_name` | Required |
| `email` | Required; must match `^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s.]{2,}$`; must be unique |
| `username` | Required; must match `^[A-Za-z0-9_][A-Za-z0-9._\-]{2,49}$` (3–50 chars) |
| `contact_number` | Required; must match `^[\d\s\-\+\(\)]{7,30}$` |
| `password` | Required; minimum 8 characters |
| `confirm_password` | Must equal `password` |

All self-registered accounts default to the `user` role.

---

## 6. Application Entry Point — app.py

`app.py` is a **single-file Flask application** (~1,220 lines). It contains:

- Bootstrap / configuration loading
- User model (`User(UserMixin)`) and helpers (`load_users`, `save_users`)
- CSRF protection helpers
- Input sanitisation helpers
- Markdown template parser (`parse_md_to_template`)
- Security response headers hook
- All route handlers
- Error handlers (403, 404, 500)
- Entry point (`if __name__ == "__main__"`)

### 6.1 Path Constants

```python
BASE_DIR    = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
LIBRARY_PATH = BASE_DIR / "config" / "bmad_library.json"
USERS_PATH  = BASE_DIR / "config" / "users.yaml"
```

### 6.2 Input Limits

```python
_MAX_NAME_LEN        = 100     # agent/report name
_MAX_SECTION_LEN     = 8192    # per-section textarea content
_MAX_MD_UPLOAD_BYTES = 512_000 # 500 KB — maximum uploaded .md file size
_MAX_SECTION_KEY_LEN = 60      # section key (snake_case heading)
_MIN_PASSWORD_LEN    = 8
```

### 6.3 Sanitisation Functions

```python
def sanitise_name(value: str) -> str:
    """Normalise an agent name to a safe, filesystem-friendly string.
    Strips special chars (keeps word chars, spaces, hyphens), replaces spaces
    with underscores, truncates to _MAX_NAME_LEN. Returns 'unnamed_agent' if empty."""

def sanitise_content(value: str) -> str:
    """Trim oversized section content to _MAX_SECTION_LEN chars."""
```

### 6.4 CSRF Protection

Manual CSRF using Flask session storage and HMAC constant-time comparison:

```python
_CSRF_TOKEN_BYTES = 32  # 256-bit token

def _csrf_token() -> str:
    """Lazily generate and store a per-session CSRF token in session['_csrf']."""

def _validate_csrf(submitted: str | None) -> bool:
    """Constant-time HMAC comparison of submitted token against session token."""
```

`_csrf_token` is registered as a Jinja2 global so templates call `{{ csrf_token() }}`.

### 6.5 Security Headers (after_request hook)

Applied to every response:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self';` |
| `Server` | *(removed)* |

### 6.6 Startup Behaviour

At startup (`if __name__ == "__main__"`):
1. Load `config.yaml` to read `web_port`.
2. Check `FLASK_DEBUG` environment variable.
3. Iterate users and warn (via `logger.warning`) if any user's password is still `changeme`.
4. Check `HTTPS_ENABLED`, `SSL_CERT_FILE`, `SSL_KEY_FILE` environment variables and build an `ssl_context` tuple if HTTPS is requested.
5. Call `app.run(host="0.0.0.0", port=_port, debug=_debug, ssl_context=_ssl_context)`.

---

## 7. Routes and Business Logic

### 7.1 `GET/POST /login`

- `GET`: Render `login.html` (redirect to `/` if already authenticated).
- `POST`:
  1. Validate CSRF token; abort 403 on failure.
  2. Read `username` and `password` from form.
  3. Call `load_users()`, look up user by username.
  4. Check password hash with `check_password_hash`.
  5. If user is suspended, flash an error and re-render the form.
  6. If valid, call `login_user(user)`.
  7. Redirect to `next` parameter (if a safe relative path) or to `/`.

### 7.2 `GET /logout`

Requires: authenticated (any role).  
Calls `logout_user()`, redirects to `/login`.

### 7.3 `GET/POST /register`

- Redirect to `/` if already authenticated.
- `POST`: Validate all registration fields (see §5.4), check username and email uniqueness, create `User`, call `save_users`, redirect to `/login`.
- Flash individual error messages on validation failure; preserve entered field values in the re-rendered form.

### 7.4 `GET/POST /change_password`

Requires: any authenticated role.  
- `POST`: Validate CSRF, check current password, validate new password (min 8 chars), confirm match, update hash in `users.yaml`, redirect to `/`.

### 7.5 `GET /`

Public (no login required).  
Load library and config; pass `templates`, `config`, and `groups` to `index.html`.

### 7.6 `GET/POST /guide/<int:template_id>`

Requires: `admin`, `super_user`, or `user` role.  
- `GET`: Look up template by index; render `guide.html` with `template`, `template_id`, `enumerated_sections` (list of `(step_idx, (key, default_value))` tuples), `total_steps`, `config`.
- `POST`:
  1. Validate CSRF; abort 403.
  2. Sanitise `agent_name` and all section values.
  3. Create output directory: `bmad_output/<agent_name>/`.
  4. For each section, write `step-{NN:02d}_{key}.md` containing `# Title\n\n{content}\n`.
  5. Write `agent.md` (master controller with checklist of shard filenames).
  6. Write `<agent_name>_complete.md` (all sections concatenated).
  7. Redirect to `/success/<agent_name>`.

**`agent.md` format:**
```
# <kind>: <agent_name> <icon>

**System Title:** <application_title>

## Overview

This <kind> was generated by <application_title>.

## Sharded Workflow

- [ ] step-00_<key>.md
- [ ] step-01_<key>.md
…
```
`<kind>` is `"Agent"` when `template.is_agent` is `True`, otherwise `"Document"`.

**`<agent_name>_complete.md` format:**
```
# <kind>: <agent_name> <icon>

**System Title:** <application_title>

## <Section Title>

<section content>

## <Section Title>

<section content>
…
```

### 7.7 `GET /dashboard`

Requires: `admin`, `super_user`, or `user`.  
Lists all subdirectory names in `bmad_output/` (sorted, excluding dotfiles).

### 7.8 `GET /success/<agent_name>`

Requires: `admin`, `super_user`, or `user`.  
Sanitise `agent_name`, list files in output directory.  
- If role is `admin`: show all files.
- Otherwise: show only `<agent_name>_complete.md`.

### 7.9 `GET /download/<agent_name>` (ZIP)

Requires: `admin` or `super_user`.  
Path-traversal guard: resolved agent dir must be inside `output_root`.  
Create a `zipfile.ZipFile(ZIP_DEFLATED)` in a `BytesIO` buffer, add all files, stream via `send_file` with `mimetype="application/zip"`.

### 7.10 `GET /download_md/<agent_name>`

Requires: `admin`, `super_user`, or `user`.  
Path-traversal guard as above.  
Serve `<agent_name>_complete.md` via `send_file` with `mimetype="text/markdown"`.

### 7.11 `POST /delete/<agent_name>`

Requires: `admin` or `super_user`.  
CSRF check; path-traversal guard; `shutil.rmtree`; redirect to `/dashboard`.

### 7.12 `GET/POST /amend/<int:template_id>`

Requires: `admin`.  
- `GET`: Render `amend.html` with template, all configured groups.
- `POST`: CSRF check; update `sections` and `groups` in memory; strip injected `id` fields; write back to `bmad_library.json` with `json.dump(..., indent=2, ensure_ascii=False)`; redirect to `/`.

### 7.13 `GET/POST /import`

Requires: `admin`.  
- `GET`: Render `import.html` with all configured groups.
- `POST`:
  1. CSRF check.
  2. Validate uploaded file: must have filename, must end with `.md`, must be ≤ 500 KB, must decode as UTF-8.
  3. Call `parse_md_to_template(md_text)` to extract name, is_agent, groups, sections.
  4. If sections are empty, flash warning and re-render.
  5. Form-selected groups override frontmatter groups (when any submitted).
  6. Form `is_agent` radio overrides frontmatter value when present.
  7. Check if a template with the same name already exists; overwrite if so, otherwise append.
  8. Write updated library to `bmad_library.json`; redirect to `/`.

### 7.14 Admin User Management Routes

All require `admin` role and CSRF validation on POST:

| Route | Method | Action |
|---|---|---|
| `/admin/users` | GET | Render `admin_users.html` with all users |
| `/admin/users/<u>/suspend` | POST | Toggle `suspended` flag; cannot suspend own account |
| `/admin/users/<u>/delete` | POST | Remove user from `users.yaml`; cannot delete own account |
| `/admin/users/<u>/role` | POST | Change role; validate against `ROLE_PERMISSIONS.keys()`; cannot change own role |
| `/admin/users/<u>/set_password` | POST | Set any user's password; validates length ≥ 8 and confirmation match |

### 7.15 `GET /view_file/<agent_name>/<filename>`

Requires: `admin`, `super_user`, or `user`.  
- Accept only `.md` files (check extension).
- Non-admin users may only view `<agent_name>_complete.md`; others are 403.
- Double path-traversal guard: agent_dir inside output_root, then file_path inside agent_dir.
- Serve with `mimetype="text/plain; charset=utf-8"`.

### 7.16 Error Handlers

```python
@app.errorhandler(403)  # renders error.html with code=403, message="Forbidden"
@app.errorhandler(404)  # renders error.html with code=404, message="Not Found"
@app.errorhandler(500)  # renders error.html with code=500, message="Internal Server Error"
```

---

## 8. BMAD v6 Sharding Engine

### 8.1 Markdown Template Parser (`parse_md_to_template`)

Parses a BMAD v6 Markdown file uploaded via `/import` and returns a template dict.

**Expected format (with optional YAML frontmatter):**

```markdown
---
name: Template Name
is_agent: true
groups:
  - Planning
  - Development
---

# Template Name

## Section One
Content for section one.

## Section Two
Content for section two.
```

**Parsing rules:**

1. If the file starts with `---`, parse the YAML block up to the closing `---` for `name`, `is_agent`, and `groups` (frontmatter values take precedence over body).
2. Parse remaining lines:
   - `# Heading` → becomes `name` if not already set via frontmatter.
   - `## Heading` → opens a new section; key is `_to_section_key(heading)`.
   - `is_agent: true` (case-insensitive line) → sets `is_agent = True`.
   - `is_agent: false` (case-insensitive line) → sets `is_agent = False`.
   - Other lines → appended to the current section's content.
3. Section content is trimmed to `_MAX_SECTION_LEN` (8,192) characters.
4. Default `name` = `"Imported Template"`, default `is_agent` = `True`.

**`_to_section_key(heading)`:**

Normalises a Markdown heading to a snake_case key:
1. Strip whitespace.
2. Remove characters not in `[\w\s\-]`.
3. Lowercase, replace spaces and hyphens with `_`, collapse consecutive `_`.
4. Truncate to `_MAX_SECTION_KEY_LEN` (60) characters.
5. Return `"section"` if empty.

### 8.2 Output Generation

All output is written to `bmad_output/<sanitised_agent_name>/`:

```
get_output_dir() / agent_name /
├── agent.md                  ← master controller
├── step-00_<key>.md          ← shard for section 0
├── step-01_<key>.md          ← shard for section 1
├── step-NN_<key>.md          ← shard for section N
└── <agent_name>_complete.md  ← full amalgamated document
```

`get_output_dir()` resolves the path from `config.base_location`, verifies it is inside `BASE_DIR` (path-traversal guard), creates the directory if needed, and returns the resolved `Path`.

---

## 9. Template Library

### 9.1 Library Format

`config/bmad_library.json` is a JSON array. See §4.3 for the schema.

The library is loaded via `load_library()`:
- Reads the JSON file.
- Injects a zero-based integer `id` into each entry.
- Ensures every entry has a `groups` key (backwards compatibility with older entries that omit it).

When saving (amend or import routes), the injected `id` field is stripped before writing:

```python
raw_templates = [{k: v for k, v in t.items() if k != "id"} for t in templates]
```

Writes are atomic Python file writes (open → write → close).

### 9.2 Section Keys

Section keys in `bmad_library.json` are snake_case strings. The UI displays them as title-cased labels:

```python
key.replace("_", " ").title()
```

Generated shard filenames follow the pattern `step-{NN:02d}_{key}.md`.

---

## 10. HTML Templates (Jinja2)

All templates extend `base.html`.

### 10.1 `base.html`

Provides:
- `<head>` with `dashboard.css` link.
- Navigation bar:
  - Brand: `{{ config.icon }} {{ config.application_title }}`
  - Links: **Templates** (`/`), **Dashboard** (`/dashboard`)
  - If authenticated: show username/role, **🔑 Change Password**, **🚪 Logout**
  - If admin: also show **👥 Users** (`/admin/users`)
  - If unauthenticated: show **Login** link
- Flash messages block (categories map to CSS classes: `alert-danger`, `alert-success`, `alert-warning`, `alert-info`).
- `{% block content %}` placeholder.
- Footer: `"BMAD v6 Template Architect — Generating sharded AI agents since 2024"`.

### 10.2 `index.html`

- Filter bar with group chips (client-side JS filtering via `filter.js`).
  - First chip: **Select All** (`data-group="__all__"`) — active by default.
  - One chip per group from `config.groups`.
- Template grid (`#template-grid`): one card per template.
  - Card has CSS class `card-agent` or `card-doc` based on `t.is_agent`.
  - Card `data-groups` attribute = comma-separated group names.
  - Card shows: type badge, template name, group tags, section count, section name list.
  - **▶ Start Guide** button links to `/guide/<t.id>`.
  - **✏ Edit Defaults** button (admin only) links to `/amend/<t.id>`.
- **📥 Import Template / Agent** button (admin only) links to `/import`.
- `<p id="no-match-msg">` hidden by default; shown by JS when no cards match the filter.
- Loads `static/js/filter.js`.

### 10.3 `login.html`

Form (POST to `/login`):
- Hidden `_csrf` field: `{{ csrf_token() }}`
- `username` text input (max 100 chars)
- `password` password input
- **🔐 Sign In** submit button
- Link to `/register`

### 10.4 `register.html`

Form (POST to `/register`):
- `_csrf` hidden field
- `full_name`, `email`, `username`, `contact_number`, `password`, `confirm_password` inputs
- Pre-fill non-sensitive fields from `form` dict passed by the route on validation failure
- **✅ Create Account** submit button

### 10.5 `change_password.html`

Form (POST to `/change_password`):
- `_csrf`, `current_password`, `new_password`, `confirm_password`
- **🔑 Change Password** submit button

### 10.6 `guide.html`

Form (POST to `/guide/<template_id>`):
- `_csrf` hidden field
- **Step 0**: `agent_name` text input (pre-filled with `template.name`, max 100 chars), labelled "Report Name".
- **Steps 1…N**: for each `(step_idx, (key, default_value))` in `enumerated_sections`:
  - `<h3>Step {{ step_idx + 1 }} of {{ total_steps }}: {{ key.replace('_', ' ').title() }}</h3>`
  - Note text: `This section will be saved as step-{NN}_{key}.md…`
  - `<textarea name="{{ key }}" rows="8" maxlength="8192">{{ default_value }}</textarea>`
- **✅ Generate BMAD v6 Document** submit button
- **← Back to Templates** link

### 10.7 `dashboard.html`

Lists all generated agent/document folder names from `agents` list.  
Each entry provides links to view the agent's files and (for super_user/admin) download ZIP.

### 10.8 `success.html`

Shows `agent_name` and the list of `files` generated:
- For all roles: **📄 Download Markdown** button (`/download_md/<agent_name>`)
- For super_user/admin: **⬇ Download ZIP** button (`/download/<agent_name>`)
- File list (for admin: all files including shards; for other roles: only `_complete.md`)

### 10.9 `amend.html`

Form (POST to `/amend/<template_id>`):
- `_csrf`, group checkboxes (one per configured group; pre-checked if in `template.groups`), one textarea per section with current default content.
- **💾 Save Defaults** submit button.

### 10.10 `import.html`

Form (POST to `/import`, `enctype="multipart/form-data"`):
- `_csrf`, file input (`accept=".md"`), group checkboxes, `is_agent` radio (`true`/`false`).
- **📥 Import Template** submit button.

### 10.11 `admin_users.html`

Table of all users:
- Columns: username, full name, email, role, status.
- Actions per user (not own account): **Suspend/Unsuspend** (`/admin/users/<u>/suspend`), **Delete** (`/admin/users/<u>/delete`), role change dropdown (`/admin/users/<u>/role`), **🔑 Set Password** expandable form (`/admin/users/<u>/set_password`).
- All actions use POST forms with `_csrf` hidden field.

### 10.12 `error.html`

Displays `code` and `message` with a back link to `/`.

---

## 11. Static Assets

### 11.1 `static/css/dashboard.css`

Provides the dark-mode UI for all pages. Key CSS classes/elements:

| Class / Element | Purpose |
|---|---|
| `body` | Dark background (`#1a1a2e`), light text (`#e0e0e0`), system font stack |
| `.nav-bar` | Top navigation bar (dark navy `#16213e`) |
| `.nav-brand` | Application title in nav |
| `.nav-links` | Right-aligned nav links |
| `.nav-user` | Username display in nav |
| `.nav-role` | Role label in nav (muted colour) |
| `.btn-logout` | Red logout button |
| `.container` | Main content area (max-width centred) |
| `.alert` | Flash message container |
| `.alert-danger` | Red flash (errors) |
| `.alert-success` | Green flash |
| `.alert-warning` | Orange flash |
| `.card-grid` | CSS Grid layout for template cards |
| `.card` | Individual template card (dark surface, rounded corners) |
| `.card-agent` | Blue-tinted left border for agent cards |
| `.card-doc` | Purple-tinted left border for document cards |
| `.card-header` | Card title area |
| `.card-type-badge` | Small badge showing "Agent" or "Document" |
| `.card-body` | Card content area |
| `.card-actions` | Card button row |
| `.card-groups` | Group tag container |
| `.group-tag` | Individual group chip/tag |
| `.btn-primary` | Primary action button (blue) |
| `.btn-secondary` | Secondary action button (muted) |
| `.filter-bar` | Group filter toolbar on index page |
| `.filter-chips` | Container for filter chip buttons |
| `.filter-chip` | Individual filter chip; `.active` class applied to selected chip |
| `.section-guide` | Section container on guide page |
| `.section-textarea` | Full-width textarea for section content |
| `.text-input` | Single-line text input |
| `.form-field` | Form field wrapper |
| `.form-actions` | Form submit button row |
| `.progress-label` | Step count label on guide page |
| `.footer` | Page footer (dark, centred text) |
| `table` | Data tables (users, etc.) |

### 11.2 `static/js/filter.js`

Client-side JavaScript for the group filter on the index page:

**Behaviour:**
1. Attach `click` listeners to all `.filter-chip` buttons.
2. On click, mark the clicked chip as `.active` and remove `.active` from all others.
3. If the selected group is `"__all__"`, show all `.card` elements and hide `#no-match-msg`.
4. Otherwise, show cards whose `data-groups` attribute contains the selected group string; hide the rest.
5. If no cards are visible after filtering, show `#no-match-msg`; otherwise hide it.

---

## 12. Security Architecture

### 12.1 Input Sanitisation

| Input | Constraint |
|---|---|
| Agent name | Max 100 chars; stripped to `[\w\s\-]`; spaces → underscores; fallback `"unnamed_agent"` |
| Section content | Max 8,192 chars; Jinja2 auto-escapes on render |
| CSRF token | Max 64 chars (form field); constant-time HMAC comparison |
| Password | Min 8 chars; hashed with Werkzeug scrypt (Python 3.12+) |
| Uploaded Markdown | Max 500 KB; must end with `.md`; must decode as UTF-8 |
| Section key | Derived from headings; `[\w\s\-]` only; max 60 chars |

### 12.2 Path-Traversal Protection

All file read/write operations validate resolved paths using `Path.resolve()` and `Path.relative_to()`:

```python
agent_dir = (output_root / safe_name).resolve()
agent_dir.relative_to(output_root.resolve())  # raises ValueError if outside
```

Operations that fail the guard return `403 Forbidden`.

### 12.3 CSRF Protection

All state-changing POST requests include and validate a per-session CSRF token:
- Token: `secrets.token_hex(32)` (256-bit CSPRNG).
- Stored in Flask session under key `"_csrf"`.
- Validated with `hmac.compare_digest(expected, submitted)` (constant-time).
- Token is exposed to templates via `{{ csrf_token() }}` Jinja2 global.

### 12.4 Secret Key Management

```python
_env_secret = os.environ.get("SECRET_KEY", "")
app.secret_key = _env_secret if len(_env_secret) >= 32 else secrets.token_hex(32)
```

If `SECRET_KEY` is not set, a random key is generated (sessions will not persist across restarts). A warning is logged.

### 12.5 Authentication

- Flask-Login `LoginManager` with `login_view = "login"`.
- `user_loader` reloads users from `users.yaml` on every request (no caching).
- Suspended users: `User.is_active` returns `False`; Flask-Login treats them as inactive.
- Open-redirect guard: `next` parameter accepted only if it starts with `/` and not `//`.

### 12.6 Logging

All security-relevant events are logged at `WARNING` or `INFO`:
- CSRF failures
- Failed login attempts
- Successful logins and logouts
- User registration
- Password changes
- Admin actions (suspend, delete, role change, set password)
- File operations (shard writes, ZIP downloads, Markdown downloads, deletes)
- Default password in use at startup

---

## 13. Containerisation

### 13.1 `Containerfile`

Multi-stage build compatible with both Podman and Docker:

**Stage 1 (`builder`):**
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
```

**Stage 2 (runtime):**
```dockerfile
FROM python:3.12-slim
RUN groupadd -r bmad && useradd -r -g bmad -d /app -s /sbin/nologin bmad
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=bmad:bmad app.py           ./app.py
COPY --chown=bmad:bmad config/          ./config/
COPY --chown=bmad:bmad templates/       ./templates/
COPY --chown=bmad:bmad static/          ./static/
COPY --chown=bmad:bmad agent/           ./agent/
RUN mkdir -p /app/bmad_output && chown bmad:bmad /app/bmad_output
USER bmad
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1
ENV FLASK_APP=app.py \
    FLASK_DEBUG=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
```

Security: application runs as non-root user `bmad`. `SECRET_KEY` must be injected at runtime via `--env-file` or `-e`.

### 13.2 Container Build and Run

```bash
# Build
podman build -t bmad6-architect:latest .

# Run
podman run -d \
  --name bmad6 \
  -p 8000:8000 \
  --env-file .env \
  -v ./bmad_output:/app/bmad_output:Z \
  bmad6-architect:latest
```

---

## 14. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | **Yes** (production) | random (dev fallback) | Flask session signing key; min 32 chars; must be ≥64-char hex in production |
| `FLASK_DEBUG` | No | `0` | Set to `1` for development only |
| `HTTPS_ENABLED` | No | `0` | Set to `1` to enable native TLS |
| `SSL_CERT_FILE` | No† | — | Path to PEM certificate; required when `HTTPS_ENABLED=1` |
| `SSL_KEY_FILE` | No† | — | Path to PEM private key; required when `HTTPS_ENABLED=1` |

† Required when `HTTPS_ENABLED=1`.

---

## 15. Deployment

### 15.1 Local Development

```bash
git clone https://github.com/DXCSithlordPadawan/BMAD6.git
cd BMAD6
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set SECRET_KEY in .env
python app.py
```

Default URL: `http://localhost:8000`

### 15.2 Production WSGI Server

Flask's built-in server must not be used in production. Use **Gunicorn** or **Waitress**:

```bash
gunicorn --workers 2 --bind 0.0.0.0:8000 'app:app'
# or
waitress-serve --port=8000 app:app
```

### 15.3 Reverse Proxy (nginx)

Terminate TLS at nginx and proxy to `127.0.0.1:8000`:

```nginx
server {
    listen 443 ssl http2;
    server_name bmad.internal.example.com;
    ssl_certificate     /etc/ssl/certs/bmad.crt;
    ssl_certificate_key /etc/ssl/private/bmad.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    allow 10.0.0.0/8;
    deny all;
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        client_max_body_size 1M;
    }
}
```

### 15.4 Production Checklist

- [ ] `SECRET_KEY` set to ≥64-character random hex string
- [ ] `FLASK_DEBUG=0`
- [ ] Default `admin` password changed in `config/users.yaml`
- [ ] Running behind TLS-terminating reverse proxy or `HTTPS_ENABLED=1` with valid cert
- [ ] Network access restricted to authorised users / VPN
- [ ] Container running as non-root (`USER bmad`)
- [ ] `bmad_output/` volume mounted outside container for persistence
- [ ] Application logs being collected
- [ ] Health check passing

---

## 16. Non-Functional Requirements

### 16.1 Performance

- Application is single-threaded Flask (suitable for small team internal use).
- No database; all state is stored in YAML/JSON files on the filesystem.
- `users.yaml` is reloaded on every request (acceptable for small user counts; scales poorly beyond ~100 users without refactoring to use a database).

### 16.2 Scalability

Not designed for horizontal scaling (filesystem-backed state). For multi-instance deployment, a shared volume or migration to a database backend is required.

### 16.3 Browser Compatibility

Standard HTML5 with no JavaScript framework dependencies. CSS uses modern properties (CSS Grid, custom properties). Supports all modern browsers.

### 16.4 Accessibility

- All form inputs have associated `<label>` elements.
- Flash messages use semantic `<div class="alert">` elements.
- Navigation is keyboard accessible.

### 16.5 Internationalisation

Not implemented. All UI text is in English. No i18n framework is used.

### 16.6 Logging

Standard Python `logging` module at `INFO` level by default:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

---

## 17. Complete File Inventory

| File | Description |
|---|---|
| `app.py` | Single-file Flask application (~1,220 lines) |
| `requirements.txt` | Python package dependencies |
| `Containerfile` | Podman/Docker multi-stage build definition |
| `.env.example` | Environment variable template (copy to `.env`) |
| `.gitignore` | Excludes `bmad_output/`, `venv/`, `__pycache__/`, `.env`, `*.pyc`, `*.pyo` |
| `config/config.yaml` | Application settings |
| `config/users.yaml` | User accounts (hashed passwords, roles) |
| `config/bmad_library.json` | Template library (all templates and their default section content) |
| `config/library.json` | Secondary/legacy library file (reference) |
| `config/dashboard.css` | (Legacy reference only) |
| `templates/base.html` | Base Jinja2 layout |
| `templates/index.html` | Template list with group filter |
| `templates/login.html` | Login form |
| `templates/register.html` | Self-registration form |
| `templates/change_password.html` | Change own password form |
| `templates/guide.html` | Step-by-step interview form |
| `templates/dashboard.html` | Generated agents/documents list |
| `templates/success.html` | Post-generation confirmation and download |
| `templates/amend.html` | Edit template defaults (admin) |
| `templates/import.html` | Import template from .md file (admin) |
| `templates/admin_users.html` | User management table (admin) |
| `templates/error.html` | Generic error page |
| `static/css/dashboard.css` | Dark-mode stylesheet |
| `static/js/filter.js` | Client-side group filter for index page |
| `agent/agent.md.j2` | Reference Jinja2 shard template (illustrative) |
| `scripts/import_bmad_library.sh` | Utility shell script |
| `docs/architecture.md` | System architecture with Mermaid diagrams |
| `docs/user_guide.md` | End-user walkthrough |
| `docs/api_guide.md` | Route/API reference |
| `docs/support_tasks.md` | Common support procedures |
| `docs/raci.md` | RACI responsibility matrix |
| `docs/rbac.md` | RBAC reference with authentication flows |
| `docs/security.md` | Security analysis (OWASP/NIST/DISA/CIS/FIPS) |
| `docs/maintenance.md` | Maintenance procedures |
| `docs/deployment.md` | Deployment guide |
| `docs/container_build.md` | Podman container build guide |
| `docs/bmadv6_prd.md` | This document — complete PRD |
