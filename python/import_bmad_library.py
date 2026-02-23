import json
import os
import re

import yaml

# ── MD Parsing ─────────────────────────────────────────────────────────────────

_MAX_SECTION_KEY_LEN = 60
_MAX_SECTION_CONTENT_LEN = 8192
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
    - A line matching ``is_agent: true`` (case-insensitive) anywhere in the
      body marks the template as an agent; ``is_agent: false`` marks it as a
      document.  When absent the template defaults to *agent*.
    - Section content is trimmed to ``_MAX_SECTION_CONTENT_LEN`` characters.
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
        # Detect is_agent metadata (flexible placement)
        low = line.strip().lower()
        if low == "is_agent: true":
            is_agent = True
            continue
        if low == "is_agent: false":
            is_agent = False
            continue

        # H1 → template name (first occurrence only)
        if line.startswith("# ") and name == "Imported Template":
            name = line[2:].strip() or name
            continue

        # H2 → new section
        if line.startswith("## "):
            # Flush the previous section
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()[
                    :_MAX_SECTION_CONTENT_LEN
                ]
            current_key = _to_section_key(line[3:])
            current_lines = []
            continue

        # Body line — collect into current section
        if current_key is not None:
            current_lines.append(line)

    # Flush the last section
    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()[
            :_MAX_SECTION_CONTENT_LEN
        ]

    return {"name": name, "is_agent": is_agent, "sections": sections}


# ── JSON Library Import ────────────────────────────────────────────────────────

try:
    from django.core.management.base import BaseCommand
    from your_app.models import BMADTemplate  # type: ignore[import]

    class Command(BaseCommand):
        help = "Imports a library of BMAD v6 templates from a JSON or Markdown file"

        def add_arguments(self, parser):
            parser.add_argument(
                "file_path",
                type=str,
                help="Path to a library.json file or a single .md template file",
            )

        def handle(self, *args, **options):
            path = options["file_path"]
            if not os.path.exists(path):
                self.stderr.write(f"File not found: {path}")
                return

            if path.lower().endswith(".md"):
                with open(path, "r", encoding="utf-8") as f:
                    md_text = f.read()
                items = [parse_md_to_template(md_text)]
            else:
                with open(path, "r", encoding="utf-8") as f:
                    items = json.load(f)

            for item in items:
                template, created = BMADTemplate.objects.update_or_create(
                    name=item["name"],
                    defaults={
                        "sections": item["sections"],
                        "is_agent": item.get("is_agent", True),
                    },
                )
                status = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"{status}: {template.name}"))

except ImportError:
    # Django is not installed; the parse_md_to_template helper is still available
    # for use by the Flask application directly.
    pass