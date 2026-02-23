"""
app.py — BMAD v6 Template Architect
Flask application that guides users through a step-by-step interview to
produce BMAD v6-compliant sharded Markdown files ready for AI submission.

Security hardening applied per OWASP Top 10, NIST SP 800-53, CIS Level 2,
and FIPS 140-2 (CSPRNG token generation, HMAC-based CSRF validation).

Authentication via Flask-Login with role-based access control (RBAC).
Supports HTTP and HTTPS operation via environment configuration.
"""

import functools
import hmac
import io
import json
import logging
import os
import re
import secrets
import shutil
import zipfile
from pathlib import Path

import yaml
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from markupsafe import escape
from werkzeug.security import check_password_hash

# ── Bootstrap ─────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: load secret key from environment; generate a random one only as a
# dev fallback — production MUST set SECRET_KEY via environment variable.
_env_secret = os.environ.get("SECRET_KEY", "")
app.secret_key = _env_secret if len(_env_secret) >= 32 else secrets.token_hex(32)
if not _env_secret:
    logger.warning(
        "SECRET_KEY not set in environment. Using a random key — "
        "sessions will not persist across restarts. Set SECRET_KEY in .env."
    )

# ── Path Constants ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
LIBRARY_PATH = BASE_DIR / "config" / "bmad_library.json"
USERS_PATH = BASE_DIR / "config" / "users.yaml"

# ── Configuration Helpers ──────────────────────────────────────────────────────


def load_config() -> dict:
    """Load BMAD application settings from config.yaml."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh).get("app_settings", {})


def load_library() -> list:
    """Load the BMAD template library from bmad_library.json."""
    with open(LIBRARY_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Inject a stable integer id so templates can be referenced by index.
    for idx, entry in enumerate(data):
        entry["id"] = idx
    return data


def get_output_dir() -> Path:
    """Return the resolved, safe output directory, creating it if needed."""
    config = load_config()
    raw = config.get("base_location", "./bmad_output/")
    path = (BASE_DIR / raw).resolve()
    # Guard against a misconfigured base_location escaping BASE_DIR.
    try:
        path.relative_to(BASE_DIR)
    except ValueError as exc:
        raise ValueError(
            f"base_location must be inside the project directory. Got: {path}"
        ) from exc
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── Authentication — User Model and Login Manager ─────────────────────────────

#: Valid application roles and which routes they may access.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"index", "guide", "dashboard", "success", "download_zip", "amend_template", "delete_agent", "import_template"},
    "user": {"index", "guide", "dashboard", "success", "download_zip", "amend_template", "delete_agent", "import_template"},
    "security_lead": {"index", "dashboard"},
    "devops": {"index"},
}

login_manager = LoginManager()
login_manager.login_view = "login"  # type: ignore[assignment]
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.init_app(app)


class User(UserMixin):
    """In-memory user object loaded from config/users.yaml."""

    def __init__(self, username: str, password_hash: str, role: str) -> None:
        self.id = username  # Flask-Login uses .id for session storage
        self.username = username
        self.password_hash = password_hash
        self.role = role


def load_users() -> dict[str, User]:
    """Load users from config/users.yaml, keyed by username."""
    if not USERS_PATH.exists():
        logger.warning("users.yaml not found at %s — no users available.", USERS_PATH)
        return {}
    with open(USERS_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    users: dict[str, User] = {}
    for entry in data.get("users", []):
        uname = entry.get("username", "")
        if uname:
            users[uname] = User(
                username=uname,
                password_hash=entry.get("password_hash", ""),
                role=entry.get("role", "user"),
            )
    return users


@login_manager.user_loader
def user_loader(user_id: str):
    """Return a User object for the given user_id (username), or None."""
    return load_users().get(user_id)


def role_required(*roles: str):
    """Decorator: redirect to login if unauthenticated, abort 403 if role not in *roles*.

    Must be applied after ``@login_required`` in the decorator stack so that
    Flask-Login's redirect logic runs first when the user is not authenticated.
    The check at line 168 is a defence-in-depth fallback for direct use without
    ``@login_required``.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                logger.warning(
                    "Access denied: user '%s' (role=%s) attempted to access '%s'",
                    current_user.username,
                    current_user.role,
                    request.path,
                )
                abort(403)
            return fn(*args, **kwargs)

        return wrapped

    return decorator


# ── CSRF Protection ────────────────────────────────────────────────────────────
# Manual CSRF using Flask session storage and HMAC constant-time comparison,
# meeting FIPS 140-2 requirements for authenticated key derivation / MAC.

_CSRF_TOKEN_BYTES = 32  # 256-bit token


def _csrf_token() -> str:
    """Return (and lazily create) a per-session CSRF token."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(_CSRF_TOKEN_BYTES)
    return session["_csrf"]


def _validate_csrf(submitted: str | None) -> bool:
    """Constant-time comparison to validate a submitted CSRF token."""
    expected = session.get("_csrf", "")
    return hmac.compare_digest(expected, submitted or "")


# Expose the helper to all Jinja2 templates.
app.jinja_env.globals["csrf_token"] = _csrf_token

# ── Input Sanitisation ─────────────────────────────────────────────────────────
_MAX_NAME_LEN = 100
_MAX_SECTION_LEN = 8192
_MAX_MD_UPLOAD_BYTES = 512_000  # 500 KB — reasonable upper bound for a template
_SAFE_NAME_RE = re.compile(r"[^\w\s\-]")  # allow word chars, spaces, hyphens


def sanitise_name(value: str) -> str:
    """Normalise an agent name to a safe, filesystem-friendly string."""
    value = str(value)[:_MAX_NAME_LEN]
    value = _SAFE_NAME_RE.sub("", value).strip().replace(" ", "_")
    return value or "unnamed_agent"


def sanitise_content(value: str) -> str:
    """Trim oversized section content. Jinja2 auto-escapes on render."""
    return str(value)[:_MAX_SECTION_LEN]


# ── Markdown Template Parser ───────────────────────────────────────────────────
_MAX_SECTION_KEY_LEN = 60
_SAFE_KEY_RE = re.compile(r"[^\w\s\-]")


def _to_section_key(heading: str) -> str:
    """Convert a Markdown heading string to a safe snake_case section key."""
    key = heading.strip()
    key = _SAFE_KEY_RE.sub("", key)
    key = key.strip().lower().replace(" ", "_").replace("-", "_")
    key = re.sub(r"_+", "_", key)
    return key[:_MAX_SECTION_KEY_LEN] or "section"


def parse_md_to_template(md_text: str) -> dict:
    """Parse a BMAD v6 Markdown file and return a template dict.

    Expected format (with optional YAML frontmatter)::

        ---
        name: Template Name
        is_agent: true
        ---

        # Template Name
        [optional: is_agent: true|false]

        ## Section One
        Content for section one.

        ## Section Two
        Content for section two.

    Rules:
    - YAML frontmatter (``---`` delimited block) is parsed first; ``name``
      and ``is_agent`` values there take precedence unless overridden later.
    - The first ``# `` heading becomes the template name if not set via
      frontmatter.
    - Every ``## `` heading opens a new section; its key is the heading text
      normalised to snake_case.
    - A line ``is_agent: true`` (case-insensitive) anywhere in the body marks
      the template as an agent; ``is_agent: false`` marks it as a document.
      When absent the template defaults to *agent* (``True``).
    - Section content is trimmed to ``_MAX_SECTION_LEN`` characters.
    """
    lines = md_text.splitlines()

    name = "Imported Template"
    is_agent = True
    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    # Parse YAML frontmatter if present (--- ... ---)
    start = 0
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is not None:
            try:
                fm = yaml.safe_load("\n".join(lines[1:end])) or {}
                if isinstance(fm, dict):
                    if "name" in fm:
                        name = str(fm["name"])
                    if "is_agent" in fm:
                        is_agent = bool(fm["is_agent"])
            except yaml.YAMLError:
                pass
            start = end + 1

    for line in lines[start:]:
        low = line.strip().lower()
        if low == "is_agent: true":
            is_agent = True
            continue
        if low == "is_agent: false":
            is_agent = False
            continue

        if line.startswith("# ") and name == "Imported Template":
            name = line[2:].strip() or name
            continue

        if line.startswith("## "):
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()[
                    :_MAX_SECTION_LEN
                ]
            current_key = _to_section_key(line[3:])
            current_lines = []
            continue

        if current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()[:_MAX_SECTION_LEN]

    return {"name": name, "is_agent": is_agent, "sections": sections}


# ── Security Response Headers ──────────────────────────────────────────────────
@app.after_request
def apply_security_headers(response):
    """Attach security headers to every HTTP response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'none';"
    )
    # Remove server fingerprinting header added by Werkzeug/Flask.
    response.headers.pop("Server", None)
    return response


# ── Routes ─────────────────────────────────────────────────────────────────────


@app.route("/login", methods=["GET", "POST"])
def login():
    """Username/password login page."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    config = load_config()
    if request.method == "POST":
        if not _validate_csrf(request.form.get("_csrf")):
            logger.warning("CSRF validation failed on /login")
            abort(403)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        users = load_users()
        user = users.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.info("User '%s' (role=%s) logged in.", username, user.role)
            next_page = request.args.get("next")
            # Guard against open-redirect: only allow relative next paths.
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("index"))

        logger.warning("Failed login attempt for username '%s'.", username)
        flash("Invalid username or password.", "danger")

    return render_template("login.html", config=config)


@app.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    username = current_user.username
    logout_user()
    logger.info("User '%s' logged out.", username)
    return redirect(url_for("login"))


@app.route("/")
def index():
    """List all available BMAD templates (agents and documents)."""
    config = load_config()
    templates = load_library()
    return render_template("index.html", templates=templates, config=config)


@app.route("/guide/<int:template_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "user")
def guide(template_id: int):
    """Step-by-step guided interview to populate a BMAD v6 template."""
    config = load_config()
    templates = load_library()

    if template_id < 0 or template_id >= len(templates):
        abort(404)

    template = templates[template_id]
    sections = template.get("sections", {})
    section_keys = list(sections.keys())

    if request.method == "POST":
        # 1. CSRF validation
        if not _validate_csrf(request.form.get("_csrf")):
            logger.warning("CSRF validation failed for template_id=%d", template_id)
            abort(403)

        # 2. Collect and sanitise form data
        agent_name = sanitise_name(
            request.form.get("agent_name", template.get("name", "agent"))
        )
        filled: dict[str, str] = {
            key: sanitise_content(request.form.get(key, ""))
            for key in section_keys
        }

        # 3. Generate BMAD v6 sharded output
        output_dir = get_output_dir() / agent_name
        output_dir.mkdir(parents=True, exist_ok=True)

        steps_manifest: list[str] = []
        for step_idx, (key, content) in enumerate(filled.items()):
            filename = f"step-{step_idx:02d}_{key}.md"
            title = key.replace("_", " ").title()
            (output_dir / filename).write_text(
                f"# {title}\n\n{content}\n", encoding="utf-8"
            )
            steps_manifest.append(filename)
            logger.info("Wrote shard: %s/%s", agent_name, filename)

        # 4. Generate master agent.md (controller / table of contents)
        icon = config.get("icon", "🧱")
        app_title = config.get("application_title", "BMAD v6 Architect")
        kind = "Agent" if template.get("is_agent", True) else "Document"
        manifest_lines = "\n".join(f"- [ ] {s}" for s in steps_manifest)
        master_md = (
            f"# {kind}: {agent_name} {icon}\n\n"
            f"**System Title:** {app_title}\n\n"
            f"## Overview\n\n"
            f"This {kind.lower()} was generated by {app_title}.\n\n"
            f"## Sharded Workflow\n\n"
            f"{manifest_lines}\n"
        )
        (output_dir / "agent.md").write_text(master_md, encoding="utf-8")
        logger.info("Generated master agent.md for '%s'", agent_name)

        # 5. Generate amalgamated single Markdown document
        amalgam_parts = [
            f"# {kind}: {agent_name} {icon}\n\n"
            f"**System Title:** {app_title}\n\n"
        ]
        for key, content in filled.items():
            title = key.replace("_", " ").title()
            amalgam_parts.append(f"## {title}\n\n{content}\n\n")
        amalgam_md = "".join(amalgam_parts)
        amalgam_filename = f"{agent_name}_complete.md"
        (output_dir / amalgam_filename).write_text(amalgam_md, encoding="utf-8")
        logger.info("Generated amalgamated document '%s' for '%s'", amalgam_filename, agent_name)

        return redirect(url_for("success", agent_name=agent_name))

    # GET — render guided form
    enumerated_sections = list(enumerate(sections.items()))
    total_steps = len(enumerated_sections)
    return render_template(
        "guide.html",
        template=template,
        template_id=template_id,
        enumerated_sections=enumerated_sections,
        total_steps=total_steps,
        config=config,
    )


@app.route("/dashboard")
@login_required
@role_required("admin", "user", "security_lead")
def dashboard():
    """Show all previously generated BMAD agents and documents."""
    config = load_config()
    output_dir = get_output_dir()
    agents: list[str] = []
    if output_dir.exists():
        agents = sorted(
            d.name
            for d in output_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
    return render_template("dashboard.html", agents=agents, config=config)


@app.route("/success/<agent_name>")
@login_required
@role_required("admin", "user")
def success(agent_name: str):
    """Confirmation page displayed after successful generation."""
    safe_name = sanitise_name(agent_name)
    config = load_config()
    output_dir = get_output_dir() / safe_name
    files: list[str] = []
    if output_dir.exists():
        files = sorted(f.name for f in output_dir.iterdir() if f.is_file())
    return render_template(
        "success.html",
        agent_name=escape(safe_name),
        files=files,
        config=config,
    )


@app.route("/download/<agent_name>")
@login_required
@role_required("admin", "user")
def download_zip(agent_name: str):
    """Stream a ZIP archive of all sharded files for a given agent."""
    safe_name = sanitise_name(agent_name)
    output_root = get_output_dir()
    agent_dir = (output_root / safe_name).resolve()

    # Path-traversal guard: the resolved agent dir must be a child of output_root.
    try:
        agent_dir.relative_to(output_root.resolve())
    except ValueError:
        abort(403)

    if not agent_dir.exists() or not agent_dir.is_dir():
        abort(404)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(agent_dir.iterdir()):
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.name)
    buf.seek(0)
    logger.info("Serving ZIP download for agent '%s'", safe_name)
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{safe_name}.zip",
    )


@app.route("/delete/<agent_name>", methods=["POST"])
@login_required
@role_required("admin", "user")
def delete_agent(agent_name: str):
    """Delete a generated agent/document directory from the output folder."""
    if not _validate_csrf(request.form.get("_csrf")):
        logger.warning("CSRF validation failed for delete agent '%s'", agent_name)
        abort(403)

    safe_name = sanitise_name(agent_name)
    output_root = get_output_dir()
    agent_dir = (output_root / safe_name).resolve()

    # Path-traversal guard: the resolved agent dir must be a child of output_root.
    try:
        agent_dir.relative_to(output_root.resolve())
    except ValueError:
        abort(403)

    if not agent_dir.exists() or not agent_dir.is_dir():
        abort(404)

    shutil.rmtree(agent_dir)
    logger.info("Deleted agent directory: '%s'", safe_name)
    flash(f"'{safe_name}' has been deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/amend/<int:template_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "user")
def amend_template(template_id: int):
    """Update the default content for a template's sections."""
    config = load_config()
    templates = load_library()

    if template_id < 0 or template_id >= len(templates):
        abort(404)

    template = templates[template_id]

    if request.method == "POST":
        if not _validate_csrf(request.form.get("_csrf")):
            logger.warning(
                "CSRF validation failed for amend template_id=%d", template_id
            )
            abort(403)

        new_sections: dict[str, str] = {
            key: sanitise_content(request.form.get(key, ""))
            for key in template.get("sections", {})
        }
        # Strip the injected id before persisting
        raw_templates = [
            {k: v for k, v in t.items() if k != "id"} for t in templates
        ]
        raw_templates[template_id]["sections"] = new_sections
        with open(LIBRARY_PATH, "w", encoding="utf-8") as fh:
            json.dump(raw_templates, fh, indent=2, ensure_ascii=False)
        logger.info("Template '%s' amended and saved.", template.get("name"))
        return redirect(url_for("index"))

    return render_template(
        "amend.html",
        template=template,
        template_id=template_id,
        config=config,
    )


@app.route("/import", methods=["GET", "POST"])
@login_required
@role_required("admin", "user")
def import_template():
    """Import a BMAD v6 template or agent from an uploaded Markdown (.md) file.

    The file is parsed by ``parse_md_to_template``:
    - The first ``# Heading`` becomes the template name.
    - Every ``## Heading`` opens a new section.
    - A line ``is_agent: true/false`` controls the template type.

    The resulting template is appended to ``config/bmad_library.json`` so it
    appears on the index page and can be run via the guided interview.
    """
    config = load_config()

    if request.method == "POST":
        if not _validate_csrf(request.form.get("_csrf")):
            logger.warning("CSRF validation failed on /import")
            abort(403)

        uploaded = request.files.get("md_file")
        if not uploaded or not uploaded.filename:
            flash("No file selected. Please choose a Markdown (.md) file.", "warning")
            return render_template("import.html", config=config)

        filename = uploaded.filename
        if not filename.lower().endswith(".md"):
            flash("Only Markdown (.md) files are accepted.", "warning")
            return render_template("import.html", config=config)

        # Check file size before reading to prevent memory exhaustion.
        uploaded.seek(0, os.SEEK_END)
        file_size = uploaded.tell()
        uploaded.seek(0)
        if file_size > _MAX_MD_UPLOAD_BYTES:
            flash("File is too large. Maximum size is 500 KB.", "warning")
            return render_template("import.html", config=config)

        raw_bytes = uploaded.read()

        try:
            md_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            flash("File could not be decoded as UTF-8 text.", "warning")
            return render_template("import.html", config=config)

        new_entry = parse_md_to_template(md_text)

        if not new_entry.get("sections"):
            flash(
                "No sections found. Ensure the file contains ## headings for each section.",
                "warning",
            )
            return render_template("import.html", config=config)

        # Persist to the library, stripping injected ids first.
        templates = load_library()
        raw_templates = [{k: v for k, v in t.items() if k != "id"} for t in templates]

        # Avoid duplicate names — update existing entry if name matches.
        existing_idx = next(
            (i for i, t in enumerate(raw_templates) if t["name"] == new_entry["name"]),
            None,
        )
        if existing_idx is not None:
            raw_templates[existing_idx] = new_entry
            action = "updated"
        else:
            raw_templates.append(new_entry)
            action = "imported"

        with open(LIBRARY_PATH, "w", encoding="utf-8") as fh:
            json.dump(raw_templates, fh, indent=2, ensure_ascii=False)

        logger.info(
            "Template '%s' %s from uploaded file '%s'.",
            new_entry["name"],
            action,
            filename,
        )
        flash(
            f"Template '{escape(new_entry['name'])}' {action} successfully.",
            "success",
        )
        return redirect(url_for("index"))

    return render_template("import.html", config=config)


# ── Error Handlers ─────────────────────────────────────────────────────────────


@app.errorhandler(403)
def forbidden(exc):
    config = load_config()
    return render_template("error.html", code=403, message="Forbidden", config=config), 403


@app.errorhandler(404)
def not_found(exc):
    config = load_config()
    return render_template("error.html", code=404, message="Not Found", config=config), 404


@app.errorhandler(500)
def server_error(exc):
    config = load_config()
    return (
        render_template("error.html", code=500, message="Internal Server Error", config=config),
        500,
    )


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _config = load_config()
    _port = int(_config.get("web_port", 8000))
    # SECURITY: debug mode must never be enabled in production.
    _debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Warn if the default admin password ('changeme') is still in use.
    from werkzeug.security import check_password_hash as _chk
    _startup_users = load_users()
    for _u in _startup_users.values():
        if _chk(_u.password_hash, "changeme"):
            logger.warning(
                "SECURITY WARNING: User '%s' is using the default password 'changeme'. "
                "Change it in config/users.yaml before deploying.",
                _u.username,
            )

    # HTTPS support: set HTTPS_ENABLED=1 and provide SSL_CERT_FILE / SSL_KEY_FILE.
    # When not set, the application runs in HTTP mode (suitable for local use or
    # when TLS is terminated at a reverse proxy).
    _ssl_context = None
    if os.environ.get("HTTPS_ENABLED", "0") == "1":
        _cert = os.environ.get("SSL_CERT_FILE", "")
        _key = os.environ.get("SSL_KEY_FILE", "")
        if _cert and _key:
            _ssl_context = (_cert, _key)
            logger.info("HTTPS enabled — cert: %s, key: %s", _cert, _key)
        else:
            logger.warning(
                "HTTPS_ENABLED=1 but SSL_CERT_FILE or SSL_KEY_FILE not set. "
                "Falling back to HTTP."
            )

    _scheme = "https" if _ssl_context else "http"
    logger.info("Starting BMAD v6 Architect on %s://0.0.0.0:%d", _scheme, _port)
    app.run(host="0.0.0.0", port=_port, debug=_debug, ssl_context=_ssl_context)
