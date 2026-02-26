# User Guide — BMAD v6 Template Architect

## 1. Introduction

The **BMAD v6 Template Architect** is a browser-based tool that guides you through creating BMAD v6-compliant AI Agent and Document templates. It produces sharded Markdown files that you can download and submit to any AI model.

---

## 2. Getting Started

### Prerequisites

- Python 3.12 or later
- `pip` package manager

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/DXCSithlordPadawan/BMAD6.git
cd BMAD6

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the secret key
cp .env.example .env
# Edit .env and set a strong SECRET_KEY (min 32 chars)

# 5. Change the default admin password
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_secure_password'))"
# Paste the output hash into config/users.yaml

# 6. Start the application
python app.py
```

Open your browser at **http://localhost:8000** — you will be redirected to the login page.

---

## 3. Signing In

The application requires authentication. On first visit you will be redirected to `/login`.

1. Enter your **username** and **password**.
2. Click **🔐 Sign In**.

On successful login you are redirected to the template list. Your username and role are shown in the navigation bar. Click **🚪 Logout** to end your session.

> **Default credentials:** `admin` / `changeme`. Change this immediately — see Section 9.

---

## 4. Walkthrough

### Step 1 — Choose a Template

The home page lists all available templates, grouped by type (Agent or Document). Each template card shows its assigned functional groups as tags.

- **Agent** templates generate AI personas with personas, workflows, and constraints.
- **Document** templates generate structured Markdown documents (e.g., Project Briefs, ADRs).

Use the **Filter by Group** bar at the top of the page to narrow the list:

- Click any group chip (e.g. *Planning*, *Development*) to show only templates in that group.
- Click **Select All** (the default) to remove the filter and show all templates.

Click **▶ Start Guide** on any template card.

### Step 2 — Complete the Interview

The guide page presents each template section as a numbered step.

1. **Step 0 — Output Name**: Enter a unique name. This becomes the folder name inside `bmad_output/`.
2. **Step 1 … N — Sections**: Fill in or amend the pre-populated text for each section.
   - Each section will be saved as a separate Markdown shard.
   - Sections are limited to 8,192 characters each.

Click **✅ Generate BMAD v6 Document** when all sections are complete.

### Step 3 — Download Your Output

The success page shows a list of generated files:

```
agent.md                        ← master controller / table of contents
step-00_<section>.md
step-01_<section>.md
…
<agent_name>_complete.md        ← consolidated single-file document
```

Two download options are available:

| Button | Description |
|---|---|
| **⬇ Download ZIP** | All sharded files as a single ZIP archive |
| **📄 Download Markdown** | The consolidated `<agent_name>_complete.md` file — ready to paste into any AI model |

### Step 4 — Submit to an AI Model

**Option A — Sharded workflow:**
1. Extract the ZIP.
2. Open `agent.md` in a text editor or paste it directly into your AI model's system prompt.
3. Paste additional step files as required context, following the checklist in `agent.md`.

**Option B — Single document:**
1. Download the Markdown file using **📄 Download Markdown**.
2. Open the file and paste its entire contents into your AI model's input.

---

## 5. Dashboard

The **Dashboard** (`/dashboard`) lists all previously generated agents and documents. From here you can:

- **View** the file list for any agent.
- **Download ZIP** of any agent's shards.

---

## 6. Editing Template Defaults

If you regularly use a template but always change the same text, you can update the default content and assigned groups:

1. On the home page, click **✏ Edit Defaults** on any template card.
2. **Groups**: Check or uncheck functional groups to control how the template is categorised and filtered.
3. Update the pre-filled text for any section.
4. Click **💾 Save Defaults**.

Changes are saved back to `config/bmad_library.json`.

---

## 7. Configuration

Edit `config/config.yaml` to change application-wide settings:

```yaml
app_settings:
  application_title: "BMAD v6 Architect"
  web_port: 8000
  base_location: "./bmad_output/"
  icon: "🧱"
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
```

| Key | Description |
|---|---|
| `application_title` | Shown in the navigation bar and generated Markdown |
| `web_port` | The TCP port the server listens on |
| `base_location` | Where generated agent folders are stored |
| `icon` | Emoji icon shown in the UI |
| `groups` | Amendable list of functional group labels used to categorise templates |

### Adding or Renaming Groups

Edit the `groups` list in `config/config.yaml`. New group names become available immediately in the filter bar and in the Edit Defaults / Import pages. Existing templates retain their assigned groups even if a group name is later removed from the list; they will simply not match the removed group filter.

---

## 8. Adding Custom Templates

### Via the Import Page (recommended)

1. Navigate to **📥 Import Template / Agent** on the home page.
2. Upload a `.md` file following the format below.
3. Optionally select one or more **Groups** in the form — these override any groups declared in the file's frontmatter.
4. Click **📥 Import Template**.

> **Note:** If a template with the same name already exists it will be **overwritten** automatically.

**Recommended Markdown format (with YAML frontmatter):**

```markdown
---
name: My Custom Agent
is_agent: true
groups:
  - Planning
  - Development
---

# My Custom Agent

## Persona
Default persona text…

## Workflow
Default workflow text…

## Constraints
Default constraints text…
```

### Via `bmad_library.json` directly

Edit `config/bmad_library.json` to add your own templates:

```json
{
  "name": "My Custom Agent",
  "is_agent": true,
  "groups": ["Planning", "Development"],
  "sections": {
    "persona": "Default persona text…",
    "workflow": "Default workflow text…",
    "constraints": "Default constraints text…"
  }
}
```

- Set `"is_agent": false` for Document templates.
- `"groups"` may be an empty list `[]` or omitted — such templates appear under **Select All** but not under any specific group filter.
- Restart the application for changes to take effect (if not using Edit Defaults in the UI).

---

## 9. User Management

### 9.1 Changing Your Own Password

Any logged-in user can change their own password at `/change_password` (accessible via the **🔑 Change Password** link in the navigation bar).

1. Enter your **current password**.
2. Enter a **new password** (minimum 8 characters).
3. **Confirm** the new password.
4. Click **🔑 Change Password**.

On success you will be redirected to the template list.

### 9.2 Admin: Setting a User's Password

Administrators can set any user's password without knowing the current password via the **👥 Users** page (`/admin/users`).

1. Navigate to **👥 Users** in the navigation bar.
2. Find the user in the table.
3. Click **🔑 Set Password** to expand the password form.
4. Enter and confirm the new password (minimum 8 characters).
5. Click **✅ Set Password**.

### 9.3 Managing Users via `config/users.yaml`

User accounts are defined in `config/users.yaml`. To add or change a user manually:

1. Generate a password hash:
   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('new_password'))"
   ```
2. Edit `config/users.yaml` and add or update the entry:
   ```yaml
   users:
     - username: myuser
       password_hash: "<paste hash here>"
       role: user   # valid roles: user, super_user, admin
   ```
3. Save the file — no restart required.

See [`docs/rbac.md`](rbac.md) for a full description of roles and permissions.

---

## 10. Frequently Asked Questions

**Q: Where are generated files stored?**
A: In `bmad_output/<agent_name>/` relative to the project root. This directory is gitignored.

**Q: Can I add more section fields?**
A: Yes — add keys to the `sections` object in `bmad_library.json`. Each key becomes a step in the guided interview.

**Q: The application won't start and says "SECRET_KEY not set".**
A: Copy `.env.example` to `.env` and set `SECRET_KEY` to a random string of at least 32 characters.

**Q: How do I run on a different port?**
A: Change `web_port` in `config/config.yaml`.

**Q: How do I enable HTTPS?**
A: Set `HTTPS_ENABLED=1`, `SSL_CERT_FILE`, and `SSL_KEY_FILE` in your `.env` file. See [`docs/deployment.md`](deployment.md) for details.

**Q: I've forgotten the admin password.**
A: Generate a new hash with `werkzeug.security.generate_password_hash` and replace the `password_hash` value in `config/users.yaml`.

**Q: I imported a template but want to update it.**
A: Simply import a new `.md` file with the same template name — it will overwrite the existing entry.

**Q: How do I filter templates by more than one group?**
A: The filter currently shows templates belonging to the selected group. Click **Select All** to see all templates, then click a different group to switch the filter.

**Q: How do I download a generated document for AI submission?**
A: On the success page after generation, click **📄 Download Markdown** to save the consolidated `<agent_name>_complete.md` file. You can then paste its contents directly into any AI model.

