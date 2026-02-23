# 🧱 BMAD v6 Template Architect

A Django-powered factory for generating sharded AI Agent and Document templates. This tool guides users through a structured interview process to produce modular, BMAD v6-compliant Markdown files.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and enter the architect
git clone [https://github.com/your-repo/bmad-architect.git](https://github.com/your-repo/bmad-architect.git)
cd bmad-architect

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

This `README.md` is designed to be the "source of truth" for your team. It explains not only how to run the Django app but also the **BMAD v6 logic** behind the files it generates.

---

### 📄 README.md

```markdown
# 🧱 BMAD v6 Template Architect

A Django-powered factory for generating sharded AI Agent and Document templates. This tool guides users through a structured interview process to produce modular, BMAD v6-compliant Markdown files.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and enter the architect
git clone [https://github.com/your-repo/bmad-architect.git](https://github.com/your-repo/bmad-architect.git)
cd bmad-architect

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

### 2. Configuration

The application is controlled by `config.yaml`. Update this file to change the output directory or the application icon.

```yaml
app_settings:
  application_title: "BMAD v6 Architect"
  web_port: 8000
  base_location: "./bmad_output/"  # Where your agents are saved
  icon: "🧱"

```

### 3. Initialize Library

Populate your local database with the starter library of agents (SDR, Product Owner, Mary the Analyst).

```bash
python manage.py migrate
python manage.py import_bmad_library bmad_library.json
python manage.py runserver 8000

```

---

## 🧠 The BMAD v6 Logic

### Sharding Architecture

This tool follows the **v6 Sharding Principle**. Instead of one large `agent.md`, it generates a folder containing:

* **`agent.md`**: The master controller (Brain).
* **`step-01_role.md`**: Persona and base constraints.
* **`step-02_workflow.md`**: The sequence of operations.
* **`step-03_output.md`**: Formatting and delivery rules.

### Why Sharding?

1. **Token Efficiency:** Only load the relevant "step" into the AI's context when needed.
2. **Modular Edits:** Amend the `workflow.md` without risking corruption of the `persona.md`.
3. **Collaboration:** Different team members can refine different "shards" of an agent simultaneously.

---

## 🛠️ Features

* **Interactive Interview:** Section-by-section guidance on what to insert into each template.
* **Import & Amend:** Import existing `.json` libraries and tweak them for your project.
* **ZIP Export:** Download fully sharded folders directly from the dashboard.
* **Dark Mode UI:** A professional interface designed for long-form prompt engineering.

## 📁 Directory Structure

```text
.
├── bmad_output/          # Generated agents (auto-created)
├── core/
│   ├── models.py         # BMADTemplate & JSONField logic
│   ├── views.py          # The Sharding & ZIP engine
│   └── utils.py          # YAML config parser
├── bmad_library.json     # Pre-made agent templates
└── config.yaml           # Global app settings

```

```

---

### 🎨 Finishing Touches
With this `README.md`, your project is now "AI-Ready." If you open this folder in an AI-powered IDE like **Cursor** or **Windsurf**, the AI will read this file and immediately understand how to help you create new templates or troubleshoot the sharding logic.

**Would you like me to generate a simple `Dockerfile` and `docker-compose.yml` so you can deploy this entire architect as a containerized service?**

```