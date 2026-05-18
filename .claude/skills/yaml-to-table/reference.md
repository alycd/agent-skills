# yaml-to-table Reference

## yaml_to_html_table.py — Internal API

### Public function

```python
yaml_to_html_table(yaml_text: str, gradient_hex: str | None = None) -> str
```

Returns a `<table>` HTML string. Raises `yaml.YAMLError` on invalid input.

### Internal helpers

| Function | Purpose |
|---|---|
| `_convert_array(arr)` | List → table cell dict. If all elements are dicts, unions keys into headers. Otherwise returns raw scalar. |
| `_convert_object(obj)` | Dict → two-column `{key, value}` table cell dict. |
| `_render_cell(cell, gradient_rgb)` | Cell dict → HTML fragment. Handles bool (green/red badge), null (grey italic), number (monospace), nested table (recursive). |
| `_render_table(table_data, gradient_rgb)` | Full `<table>` HTML from a table cell dict. Applies gradient if `gradient_rgb` is set. |
| `_hex_to_rgb(hex_color)` | `#RRGGBB` or `#RGB` → `(r, g, b)` int tuple. |
| `_is_light(r, g, b)` | Luminance check — returns True if color is light (use dark text). |
| `_tint(r, g, b, factor)` | Blend toward white by factor (0 = full color, 1 = white). |

### Cell dict schema

```python
# Scalar cell
{"value": <any>}

# Table cell
{
  "value": None,
  "is_table": True,
  "headers": ["col1", "col2", ...],
  "rows": [[cell_dict, cell_dict, ...], ...]
}
```

### Gradient algorithm

Headers: left column gets `gradient_hex` at full saturation, right column gets a 40% tint toward white.
Data cells: left column 50% tint → right column 90% tint.
Text color: `#ffffff` for dark backgrounds, `#111827` for light backgrounds (luminance threshold 0.55).

---

## app.py — Flask routes

### GET /

Serves `templates/index.html` via `render_template`.

### POST /api/render

```
Content-Type: application/json

{
  "url"?:       string   — fetched with requests.get(timeout=10)
  "yaml_text"?: string   — used directly if no url
  "color"?:     string   — passed as gradient_hex to yaml_to_html_table
}
```

Priority: `url` takes precedence over `yaml_text` when both are supplied.

Error conditions returned as `{"error": "..."}`:
- No url and no yaml_text
- Request timeout (10 s)
- HTTP error (4xx/5xx)
- Connection error
- YAML parse error

---

## yaml_to_table.py — Legacy CLI (original tool)

Requires `oyaml` and `prettytable` (not in requirements.txt — install separately if needed):
```bash
pip install oyaml prettytable
```

Generates a four-column documentation scaffold: **Field | Example Value | Required | Description** (Description is Lorem ipsum placeholder).

Output modes:
- `--out txt` — PrettyTable to stdout
- `--out html` — Bootstrap-styled HTML saved as `<input>.doc.html`

---

## requirements.txt

```
flask>=3.0
requests>=2.31
pytest>=8.0
pyyaml>=6.0
```

`oyaml` and `prettytable` are only needed for the legacy `yaml_to_table.py` tool.

---

## Test suite (tests/test_app.py)

Located in the source repo at `/Users/alysidi/git/aly/yaml-to-table/tests/test_app.py`.

Tests covered:
1. GET / returns 200
2. YAML text → HTML table
3. List of dicts → wide table
4. Color param → gradient applied
5. Empty body → error
6. Invalid YAML → error
7. URL fetch (mocked) → HTML
8. URL timeout → error
9. Connection error → error
10. HTTP error (404) → error

Run: `pytest tests/`
