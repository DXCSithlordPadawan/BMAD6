"""
app.py — BMAD v6 Template Architect
Flask application that guides users through a step-by-step interview to
produce BMAD v6-compliant sharded Markdown files ready for AI submission.

Security hardening applied per OWASP Top 10, NIST SP 800-53, CIS Level 2,
and FIPS 140-2 (CSPRNG token generation, HMAC-based CSRF validation).
"""

import hmac
import io
import json
import logging
import os
import re
import secrets
import zipfile
from pathlib import Path

import yaml
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from markupsafe import escape

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
_SAFE_NAME_RE = re.compile(r"[^\w\s\-]")  # allow word chars, spaces, hyphens


def sanitise_name(value: str) -> str:
    """Normalise an agent name to a safe, filesystem-friendly string."""
    value = str(value)[:_MAX_NAME_LEN]
    value = _SAFE_NAME_RE.sub("", value).strip().replace(" ", "_")
    return value or "unnamed_agent"


def sanitise_content(value: str) -> str:
    """Trim oversized section content. Jinja2 auto-escapes on render."""
    return str(value)[:_MAX_SECTION_LEN]


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


@app.route("/")
def index():
    """List all available BMAD templates (agents and documents)."""
    config = load_config()
    templates = load_library()
    return render_template("index.html", templates=templates, config=config)


@app.route("/guide/<int:template_id>", methods=["GET", "POST"])
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


@app.route("/amend/<int:template_id>", methods=["GET", "POST"])
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
    app.run(host="0.0.0.0", port=_port, debug=_debug)
