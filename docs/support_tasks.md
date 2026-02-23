# Support Tasks — BMAD v6 Template Architect

## 1. Application Won't Start

**Symptom:** `python app.py` exits immediately or returns a Flask startup error.

**Checklist:**

1. Confirm Python version: `python --version` — must be 3.12+.
2. Confirm dependencies are installed: `pip install -r requirements.txt`.
3. Check that `config/config.yaml` exists and is valid YAML.
4. Check that `config/bmad_library.json` exists and is valid JSON.
5. Confirm `.env` exists or `SECRET_KEY` is exported: `echo $SECRET_KEY`.
6. Check the port is not in use: `ss -tlnp | grep 8000` (or the configured port).

---

## 2. CSRF Errors (403 Forbidden)

**Symptom:** Submitting a form returns a `403 Forbidden` page.

**Cause:** The CSRF token in the submitted form does not match the session token.

**Resolution:**

- Ensure cookies are enabled in the browser.
- Do not open the form in multiple tabs simultaneously and submit from an old tab.
- If using a reverse proxy (nginx, Traefik), ensure it forwards cookies correctly.
- If `SECRET_KEY` changes between the time the form was rendered and submitted, the session is invalidated. Ensure `SECRET_KEY` is stable (set in `.env`, not auto-generated).

---

## 3. Generated Files Not Appearing in Dashboard

**Symptom:** The dashboard shows "No agents generated yet" after a successful generation.

**Checklist:**

1. Check `config/config.yaml` — `base_location` must be a path relative to the project root or an absolute path that exists.
2. Confirm the application process has write permission to `bmad_output/`.
3. Check the application logs for `Wrote shard:` messages confirming files were written.

---

## 4. ZIP Download is Empty or Corrupt

**Symptom:** The downloaded ZIP file cannot be opened.

**Checklist:**

1. Confirm the agent folder exists: `ls bmad_output/<agent_name>/`.
2. Ensure no anti-virus or security tool is stripping the response in transit.
3. If running behind a reverse proxy, ensure the proxy is not buffering the streaming response.

---

## 5. Template Library Changes Not Reflected

**Symptom:** Editing `config/bmad_library.json` manually does not change what appears in the UI.

**Resolution:**

- The library is read on every request — no restart required.
- Validate the JSON is syntactically correct: `python -c "import json; json.load(open('config/bmad_library.json'))"`.

---

## 6. Container Fails to Start

See [`container_build.md`](container_build.md) for container-specific troubleshooting.

---

## 7. Resetting the Template Library

To revert `bmad_library.json` to its last committed state:

```bash
git checkout config/bmad_library.json
```

---

## 8. Log Locations

| Environment | Log output |
|---|---|
| Local (development) | stdout / terminal |
| Container (Podman) | `podman logs <container_name>` |

Log format: `YYYY-MM-DD HH:MM:SS [LEVEL] logger: message`
