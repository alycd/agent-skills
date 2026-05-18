---
name: yaml-to-table
description: Deploy and use the yaml-to-table Flask web server that renders YAML files as interactive HTML tables. Use when the user wants to: run the yaml-to-table web app, add yaml-to-table to a project, convert YAML to HTML tables via API or CLI, embed the yaml_to_html_table converter in Python code, or work with the yaml-to-table server. Triggers: "yaml to table", "yaml table", "render yaml", "yaml web server", "start yaml server", "html table from yaml", "yaml start", "start yaml", "yaml server", "yaml skill", "yaml app".
---

# yaml-to-table

A Flask web server + Python library that converts YAML into interactive HTML tables. Supports a browser UI with color gradients, a REST API, and a CLI.

## Quick start — run the server

Copy the app files into the target directory and start the server:

```bash
# 1. Copy skill files into project
cp ~/.claude/skills/yaml-to-table/scripts/app.py .
cp ~/.claude/skills/yaml-to-table/scripts/yaml_to_html_table.py .
cp ~/.claude/skills/yaml-to-table/requirements.txt .
mkdir -p templates
cp ~/.claude/skills/yaml-to-table/templates/index.html templates/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
# → http://localhost:5000
```

## Architecture

```
app.py                  Flask server (GET / and POST /api/render)
yaml_to_html_table.py   Converter library (also works as CLI)
yaml_to_table.py        Legacy CLI tool (prettytable + oyaml)
templates/index.html    Single-page UI
```

## REST API

### POST /api/render

**Request** (JSON):
| Field       | Type   | Description                              |
|-------------|--------|------------------------------------------|
| `url`       | string | Fetch YAML from a remote URL             |
| `yaml_text` | string | Inline YAML string                       |
| `color`     | string | Optional `#RRGGBB` gradient color        |

Supply either `url` or `yaml_text`, not both.

**Success response:**
```json
{ "html": "<table style=\"...\">...</table>" }
```

**Error response:**
```json
{ "error": "Provide a URL or paste YAML text." }
```

**Example curl:**
```bash
curl -s -X POST http://localhost:5000/api/render \
  -H 'Content-Type: application/json' \
  -d '{"yaml_text": "name: test\nvalue: 42", "color": "#3498db"}' | jq .
```

## Python library usage

`yaml_to_html_table.py` exports one public function:

```python
from yaml_to_html_table import yaml_to_html_table

html = yaml_to_html_table(yaml_text, gradient_hex="#3498db")
# Returns a <table>...</table> HTML string
```

Behavior:
- **List of dicts** → wide table, one column per unique key
- **Plain dict** → two-column key/value table
- **Nested values** → recursively rendered as nested `<table>` elements
- `gradient_hex=None` → monochrome (white/grey rows)
- `gradient_hex="#RRGGBB"` → left column full color fading right to near-white

## CLI usage

```bash
# Modern converter (yaml_to_html_table.py)
python yaml_to_html_table.py input.yaml -o output.html --color "#9b59b6"

# Legacy tool (yaml_to_table.py) — outputs Field/Required/Description scaffold
python yaml_to_table.py --inputFile input.yaml --out html
python yaml_to_table.py --inputFile input.yaml --out txt
```

## UI features

The browser UI at `http://localhost:5000` supports:
- **URL input** — paste any YAML URL; auto-renders on page load if `?url=` param present
- **Paste mode** — click the `── or paste YAML below ──` divider to show textarea
- **Color palette** — 20 Flat UI colors + "none" option
- **URL params** — `?url=<yaml-url>&color=%233498db` for shareable links
- **Keyboard** — Enter in URL field triggers render

## Color palette (Flat UI)

| Name        | Hex       | Name        | Hex       |
|-------------|-----------|-------------|-----------|
| Turquoise   | `#1abc9c` | Sunflower   | `#f1c40f` |
| Emerald     | `#2ecc71` | Carrot      | `#e67e22` |
| Peter River | `#3498db` | Alizarin    | `#e74c3c` |
| Amethyst    | `#9b59b6` | Orange      | `#f39c12` |
| Wet Asphalt | `#34495e` | Pumpkin     | `#d35400` |
| Green Sea   | `#16a085` | Pomegranate | `#c0392b` |
| Nephritis   | `#27ae60` | Clouds      | `#ecf0f1` |
| Belize Hole | `#2980b9` | Silver      | `#bdc3c7` |
| Wisteria    | `#8e44ad` | Concrete    | `#95a5a6` |
| Midnight    | `#2c3e50` | Asbestos    | `#7f8c8d` |

## Instructions for Claude

When deploying this app to a new project:

1. Copy `scripts/app.py`, `scripts/yaml_to_html_table.py`, and `requirements.txt` to the project root.
2. Copy `templates/index.html` to a `templates/` subdirectory.
3. Run `pip install -r requirements.txt` to install Flask, requests, pyyaml.
4. Start with `python app.py` (default port 5000) or `flask run`.
5. To run tests: copy `tests/test_app.py` from the source repo and run `pytest`.

When adding the converter to existing Python code:
1. Copy `scripts/yaml_to_html_table.py` alongside the importing module.
2. `from yaml_to_html_table import yaml_to_html_table` — that's the entire public API.
3. No Flask dependency needed; only `pyyaml` is required.

See [reference.md](reference.md) for internal module details and advanced configuration.
