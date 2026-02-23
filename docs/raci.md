# RACI Document — BMAD v6 Template Architect

**R** = Responsible | **A** = Accountable | **C** = Consulted | **I** = Informed

---

## Roles

| Role | Description |
|---|---|
| **Product Owner** | Owns the product roadmap and prioritises features |
| **Developer** | Implements and maintains the application code |
| **DevOps / Platform** | Manages deployments, containers, and infrastructure |
| **Security Lead** | Reviews and approves security posture |
| **End User** | Uses the application to generate BMAD templates |
| **Technical Writer** | Maintains documentation |

---

## RACI Matrix

| Task | Product Owner | Developer | DevOps / Platform | Security Lead | End User | Technical Writer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Define template requirements | A | C | I | I | C | C |
| Implement Flask application | I | R/A | C | C | I | I |
| Update `bmad_library.json` templates | A | R | I | I | C | C |
| Maintain `config.yaml` | A | R | C | I | I | I |
| Write unit / integration tests | I | R/A | I | C | I | I |
| Build and publish container image | I | C | R/A | C | I | I |
| Deploy to production environment | A | C | R | C | I | I |
| Security review and pen test | A | C | C | R | I | I |
| Rotate `SECRET_KEY` in production | I | C | R | A | I | I |
| Monitor application logs | I | C | R/A | C | I | I |
| Maintain documentation | I | C | I | C | I | R/A |
| Raise and triage support tickets | I | R | C | C | R | I |
| Approve production deployments | A | C | C | C | I | I |

---

## Decision Authority

| Decision | Authority |
|---|---|
| Add new template to library | Product Owner |
| Change security headers | Security Lead + Developer |
| Upgrade Python / Flask version | Developer (notifies Security Lead) |
| Change output directory | Developer + DevOps |
| Enable debug mode in production | **Prohibited** — requires Security Lead exception |
