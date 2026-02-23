# Maintenance Guide — BMAD v6 Template Architect

## 1. Routine Maintenance Tasks

### 1.1 Update Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Check for outdated packages
pip list --outdated

# Update requirements.txt (review each update for breaking changes)
pip install --upgrade Flask PyYAML python-dotenv MarkupSafe Werkzeug
pip freeze | grep -E "Flask|PyYAML|python-dotenv|MarkupSafe|Werkzeug" > requirements.txt
```

Run `python app.py` after updating to confirm the application still starts.

### 1.2 Rotate the Secret Key

The `SECRET_KEY` should be rotated at least quarterly or immediately following a suspected compromise.

```bash
# Generate a new key
python -c "import secrets; print(secrets.token_hex(32))"

# Update .env
SECRET_KEY=<new_value>

# Restart the application / container
```

> **Note:** Rotating `SECRET_KEY` invalidates all active browser sessions and any in-flight CSRF tokens. Inform users before rotating in shared environments.

### 1.3 Clean Up Generated Output

Old agent output directories can be removed manually:

```bash
# List generated agents
ls bmad_output/

# Remove a specific agent
rm -rf bmad_output/<agent_name>

# Remove all output (use with caution)
rm -rf bmad_output/*
```

---

## 2. Adding a New Template

1. Edit `config/bmad_library.json`.
2. Add a new JSON object to the array following this schema:

```json
{
  "name": "Template Name",
  "is_agent": true,
  "sections": {
    "section_key": "Default placeholder text."
  }
}
```

3. Validate the JSON: `python -c "import json; json.load(open('config/bmad_library.json'))"`.
4. Refresh the browser — no restart required.

---

## 3. Modifying the Application Configuration

Edit `config/config.yaml`. No restart required; the file is read on each request.

```yaml
app_settings:
  application_title: "BMAD v6 Architect"
  web_port: 8000
  base_location: "./bmad_output/"
  icon: "🧱"
  sharding_enabled: true
```

---

## 4. Updating the Container Image

See [`container_build.md`](container_build.md) for full build and publish steps.

Quick rebuild after a code change:

```bash
podman build -t bmad6-architect:latest .
podman stop bmad6
podman rm bmad6
podman run -d --name bmad6 -p 8000:8000 --env-file .env bmad6-architect:latest
```

---

## 5. Log Review

### Local

Application logs are written to stdout. To capture them:

```bash
python app.py 2>&1 | tee /var/log/bmad6.log
```

### Container

```bash
podman logs bmad6
podman logs --follow bmad6   # tail -f equivalent
```

Look for `[WARNING]` CSRF events which may indicate a scanning attempt or session issue.

---

## 6. Health Check

A manual health check can be performed with:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
# Expected: 200
```

In a containerised deployment, the `HEALTHCHECK` instruction in `Containerfile` runs this automatically every 30 seconds.

---

## 7. Backup Recommendations

| Item | Frequency | Method |
|---|---|---|
| `config/bmad_library.json` | After each template change | Git commit or file copy |
| `config/config.yaml` | After each config change | Git commit or file copy |
| `bmad_output/` | Weekly or after each generation session | `tar czf bmad_output_$(date +%Y%m%d).tar.gz bmad_output/` |
| `.env` | After each key rotation | Secure secrets manager (e.g., Vault, SOPS) — never git |
