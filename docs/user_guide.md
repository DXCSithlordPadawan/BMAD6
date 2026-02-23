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

# 5. Start the application
python app.py
```

Open your browser at **http://localhost:8000**.

---

## 3. Walkthrough

### Step 1 — Choose a Template

The home page lists all available templates, grouped by type (Agent or Document).

- **Agent** templates generate AI personas with personas, workflows, and constraints.
- **Document** templates generate structured Markdown documents (e.g., Project Briefs, ADRs).

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
agent.md          ← master controller / table of contents
step-00_<section>.md
step-01_<section>.md
…
```

Click **⬇ Download ZIP** to receive all files as a single archive.

### Step 4 — Submit to an AI Model

1. Extract the ZIP.
2. Open `agent.md` in a text editor or paste it directly into your AI model's system prompt.
3. Paste additional step files as required context, following the checklist in `agent.md`.

---

## 4. Dashboard

The **Dashboard** (`/dashboard`) lists all previously generated agents and documents. From here you can:

- **View** the file list for any agent.
- **Download ZIP** of any agent's shards.

---

## 5. Editing Template Defaults

If you regularly use a template but always change the same text, you can update the default content:

1. On the home page, click **✏ Edit Defaults** on any template card.
2. Update the pre-filled text for any section.
3. Click **💾 Save Defaults**.

Changes are saved back to `config/bmad_library.json`.

---

## 6. Configuration

Edit `config/config.yaml` to change application-wide settings:

```yaml
app_settings:
  application_title: "BMAD v6 Architect"
  web_port: 8000
  base_location: "./bmad_output/"
  icon: "🧱"
  sharding_enabled: true
```

| Key | Description |
|---|---|
| `application_title` | Shown in the navigation bar and generated Markdown |
| `web_port` | The TCP port the server listens on |
| `base_location` | Where generated agent folders are stored |
| `icon` | Emoji icon shown in the UI |

---

## 7. Adding Custom Templates

Edit `config/bmad_library.json` to add your own templates:

```json
{
  "name": "My Custom Agent",
  "is_agent": true,
  "sections": {
    "persona": "Default persona text…",
    "workflow": "Default workflow text…",
    "constraints": "Default constraints text…"
  }
}
```

- Set `"is_agent": false` for Document templates.
- Restart the application for changes to take effect (if not using Edit Defaults in the UI).

---

## 8. Frequently Asked Questions

**Q: Where are generated files stored?**
A: In `bmad_output/<agent_name>/` relative to the project root. This directory is gitignored.

**Q: Can I add more section fields?**
A: Yes — add keys to the `sections` object in `bmad_library.json`. Each key becomes a step in the guided interview.

**Q: The application won't start and says "SECRET_KEY not set".**
A: Copy `.env.example` to `.env` and set `SECRET_KEY` to a random string of at least 32 characters.

**Q: How do I run on a different port?**
A: Change `web_port` in `config/config.yaml`.
