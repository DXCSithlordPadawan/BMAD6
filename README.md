# 🧱 BMAD v6 Template Architect

A Python Flask web application that guides users through a structured,
step-by-step interview process to produce **BMAD v6-compliant sharded Markdown
files** ready for submission to an AI model.

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/DXCSithlordPadawan/BMAD6.git
cd BMAD6

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure (copy and edit the example env file)
cp .env.example .env
# Set SECRET_KEY to a random 64-char hex string in .env

# 5. Start
python app.py
```

Open **http://localhost:8000** in your browser.

---

## 🐳 Container (Podman)

```bash
podman build -t bmad6-architect .
podman run -d --name bmad6 -p 8000:8000 --env-file .env \
  -v ./bmad_output:/app/bmad_output:Z bmad6-architect
```

See [`docs/container_build.md`](docs/container_build.md) for full details.

---

## 🧠 BMAD v6 Sharding

Instead of one large Markdown file, the tool generates a sharded folder:

| File | Purpose |
|---|---|
| `agent.md` | Master controller — table of contents |
| `step-00_<section>.md` | First shard (e.g., Persona) |
| `step-01_<section>.md` | Second shard (e.g., Workflow) |
| `step-NN_<section>.md` | … additional shards |

Each shard can be submitted to an AI model independently, reducing token usage
while keeping the context precise.

---

## 📁 Project Structure

```
BMAD6/
├── app.py               # Flask application entry point
├── requirements.txt     # Python dependencies
├── Containerfile        # Podman / Docker multi-stage build
├── .env.example         # Environment variable template
├── config/
│   ├── config.yaml      # Application settings
│   └── bmad_library.json # Template library
├── templates/           # Jinja2 HTML templates
├── static/css/          # Dark-mode stylesheet
├── agent/               # Reference Jinja2 agent template
├── bmad_output/         # Generated agents (gitignored)
└── docs/                # Full documentation suite
```

---

## 📚 Documentation

| Document | Description |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | System architecture with Mermaid diagrams |
| [`docs/user_guide.md`](docs/user_guide.md) | End-user walkthrough |
| [`docs/api_guide.md`](docs/api_guide.md) | Route / API reference |
| [`docs/support_tasks.md`](docs/support_tasks.md) | Common support procedures |
| [`docs/raci.md`](docs/raci.md) | RACI responsibility matrix |
| [`docs/rbac.md`](docs/rbac.md) | Role-based access control |
| [`docs/security.md`](docs/security.md) | Security analysis (OWASP / NIST / DISA / CIS / FIPS) |
| [`docs/maintenance.md`](docs/maintenance.md) | Maintenance procedures |
| [`docs/deployment.md`](docs/deployment.md) | Deployment guide |
| [`docs/container_build.md`](docs/container_build.md) | Podman container build guide |
