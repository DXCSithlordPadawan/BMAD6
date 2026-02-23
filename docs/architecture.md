# Architecture Guide — BMAD v6 Template Architect

## 1. Overview

The **BMAD v6 Template Architect** is a lightweight Python Flask web application that guides users through a structured, step-by-step interview process. The output is a folder of sharded Markdown files that are **BMAD v6 compliant** and ready for submission to an AI model.

---

## 2. High-Level Architecture

```mermaid
flowchart TD
    Browser["User Browser"] -->|HTTP| Flask["Flask App (app.py)"]
    Flask -->|reads| Config["config/config.yaml"]
    Flask -->|reads / writes| Library["config/bmad_library.json"]
    Flask -->|writes shards| Output["bmad_output/<agent_name>/"]
    Flask -->|renders| Templates["templates/*.html"]
    Flask -->|serves| Static["static/css/dashboard.css"]
    Output -->|ZIP download| Browser
```

---

## 3. Component Breakdown

| Component | File(s) | Responsibility |
|---|---|---|
| **Flask App** | `app.py` | Route handling, CSRF, sharding logic, security headers |
| **Config** | `config/config.yaml` | Application settings (title, port, output dir, icon) |
| **Template Library** | `config/bmad_library.json` | Defines agent/document templates and their default section text |
| **HTML Templates** | `templates/*.html` | Jinja2 templates rendered by Flask |
| **Stylesheet** | `static/css/dashboard.css` | Dark-mode UI CSS |
| **Agent Jinja2 Template** | `agent/agent.md.j2` | Reference template for the master agent.md structure |
| **Output** | `bmad_output/<name>/` | Generated sharded Markdown files (gitignored) |
| **Container** | `Containerfile` | Podman/Docker multi-stage build for production deployment |

---

## 4. BMAD v6 Sharding Architecture

```mermaid
flowchart LR
    Form["Guided Form\n(one textarea per section)"] --> Engine["Sharding Engine\n(app.py: guide route)"]
    Engine --> S0["step-00_persona.md"]
    Engine --> S1["step-01_workflow.md"]
    Engine --> S2["step-02_constraints.md"]
    Engine --> SN["step-NN_<section>.md"]
    Engine --> Master["agent.md\n(master controller)"]
    Master -.->|references| S0
    Master -.->|references| S1
    Master -.->|references| S2
    Master -.->|references| SN
```

Each section of a template becomes a **shard** (a numbered Markdown file). The master `agent.md` contains a checklist of all shards so an AI model can load exactly the context it needs.

---

## 5. Request–Response Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant F as Flask App
    participant FS as Filesystem

    U->>F: GET /guide/<id>
    F->>FS: read config.yaml + bmad_library.json
    F-->>U: render guide.html (pre-filled form)

    U->>F: POST /guide/<id> (form data)
    F->>F: validate CSRF token
    F->>F: sanitise inputs
    F->>FS: write step-00_*.md … step-NN_*.md
    F->>FS: write agent.md
    F-->>U: redirect to /success/<agent_name>

    U->>F: GET /download/<agent_name>
    F->>FS: read agent folder
    F-->>U: stream ZIP archive
```

---

## 6. Security Architecture

```mermaid
flowchart TD
    Request["Incoming HTTP Request"] --> Headers["Security Headers\n(after_request hook)"]
    Headers --> CSRF["CSRF Token Validation\n(POST routes only)"]
    CSRF --> Input["Input Sanitisation\n(name + content)"]
    Input --> PathGuard["Path-Traversal Guard\n(resolve + relative_to)"]
    PathGuard --> Logic["Business Logic"]
    Logic --> Response["HTTP Response"]
```

See [`docs/security.md`](security.md) for the full security analysis.

---

## 7. Directory Structure

```
BMAD6/
├── app.py                   # Flask application entry point
├── requirements.txt         # Python dependencies
├── Containerfile            # Podman multi-stage container build
├── .env.example             # Environment variable template
├── .gitignore
│
├── config/
│   ├── config.yaml          # Application settings
│   └── bmad_library.json    # Template library (agents + documents)
│
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── guide.html
│   ├── dashboard.html
│   ├── success.html
│   ├── amend.html
│   └── error.html
│
├── static/
│   └── css/
│       └── dashboard.css    # Dark-mode stylesheet
│
├── agent/
│   └── agent.md.j2          # Reference Jinja2 shard template
│
├── bmad_output/             # Generated agents & documents (gitignored)
│   └── <agent_name>/
│       ├── agent.md
│       ├── step-00_*.md
│       └── step-NN_*.md
│
├── docs/                    # All project documentation
│   ├── architecture.md      ← this file
│   ├── user_guide.md
│   ├── api_guide.md
│   ├── support_tasks.md
│   ├── raci.md
│   ├── rbac.md
│   ├── security.md
│   ├── maintenance.md
│   ├── deployment.md
│   └── container_build.md
│
├── python/                  # Legacy Django code fragments (reference only)
├── html/                    # Legacy HTML fragments (reference only)
└── scripts/                 # Utility shell scripts
```

---

## 8. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.12+ |
| Web Framework | Flask | 3.0+ |
| Templating | Jinja2 | (bundled with Flask) |
| Config Parsing | PyYAML | 6.0+ |
| Env Management | python-dotenv | 1.0+ |
| HTML Sanitisation | MarkupSafe | 2.1+ |
| Containerisation | Podman | 4.x+ |
| Container Base | python:3.12-slim | (official Docker Hub) |
