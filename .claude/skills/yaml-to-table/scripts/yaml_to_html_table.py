#!/usr/bin/env python3
"""
YAML to HTML table converter — mirrors the logic from jsontotable.org/yaml-to-table.

Arrays of dicts  → table with union of all keys as headers, one row per item.
Plain dicts      → two-column key/value table.
Nested values    → recursively rendered as nested tables.
"""

import sys
import yaml
import argparse
from pathlib import Path


def _hex_to_rgb(hex_color: str):
    """Parse #RRGGBB or #RGB → (r, g, b) int tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _is_light(r, g, b) -> bool:
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55


def _tint(r, g, b, factor: float) -> str:
    """Blend (r,g,b) toward white by *factor* (0 = full color, 1 = white)."""
    tr = int(r + (255 - r) * factor)
    tg = int(g + (255 - g) * factor)
    tb = int(b + (255 - b) * factor)
    return f"#{tr:02x}{tg:02x}{tb:02x}"


# ---------------------------------------------------------------------------
# Data-structure builders  (JS equivalents: v() and w())
# ---------------------------------------------------------------------------

def _convert_array(arr):
    """Convert a list into a table cell dict.

    If every element is a plain dict, unions their keys into headers and maps
    each dict to a row.  Otherwise returns the list as a raw scalar value.
    """
    if len(arr) == 0:
        return {"value": "[]"}

    if not all(isinstance(item, dict) for item in arr):
        return {"value": arr}

    # Collect keys in first-seen order (dict.fromkeys preserves insertion order).
    headers = list(dict.fromkeys(k for item in arr for k in item.keys()))

    rows = []
    for item in arr:
        cells = []
        for h in headers:
            val = item.get(h)
            if isinstance(val, list):
                cells.append(_convert_array(val))
            elif isinstance(val, dict):
                cells.append(_convert_object(val))
            else:
                cells.append({"value": val})
        rows.append(cells)

    return {"value": None, "is_table": True, "headers": headers, "rows": rows}


def _convert_object(obj):
    """Convert a dict into a two-column key/value table cell dict."""
    headers = ["key", "value"]
    rows = []
    for k, v in obj.items():
        if isinstance(v, list):
            val_cell = _convert_array(v)
        elif isinstance(v, dict):
            val_cell = _convert_object(v)
        else:
            val_cell = {"value": v}
        rows.append([{"value": k}, val_cell])
    return {"value": None, "is_table": True, "headers": headers, "rows": rows}


# ---------------------------------------------------------------------------
# HTML rendering  (JS equivalent: ea() and the inline table JSX)
# ---------------------------------------------------------------------------

_TH_STYLE = (
    "border:1.5px solid #000;"
    "background:#f9fafb;"
    "padding:4px 8px;"
    "text-align:left;"
    "font-weight:bold;"
    "white-space:nowrap;"
)
_TD_BASE = "border:1.5px solid #000;padding:4px 8px;vertical-align:top;"
_TD_ODD  = _TD_BASE + "background:#ffffff;"
_TD_EVEN = _TD_BASE + "background:#f9fafb;"
_TABLE_STYLE = (
    "border-collapse:collapse;"
    "width:100%;"
    "font-size:0.875rem;"
)


def _render_cell(cell, gradient_rgb=None):
    """Render one cell dict to an HTML fragment string."""
    if cell.get("is_table") and cell.get("headers") and cell.get("rows") is not None:
        return _render_table(cell, gradient_rgb)

    val = cell.get("value")

    if isinstance(val, list):
        return ", ".join(str(v) for v in val)

    if val is None:
        return '<span style="color:#9ca3af;font-style:italic;">null</span>'

    if isinstance(val, bool):
        bg    = "#dcfce7" if val else "#fee2e2"
        color = "#15803d" if val else "#b91c1c"
        label = "true" if val else "false"
        return (
            f'<span style="background:{bg};color:{color};'
            f'padding:1px 6px;border-radius:3px;font-size:0.85em;font-weight:500;">'
            f"{label}</span>"
        )

    if isinstance(val, (int, float)):
        return f'<span style="font-family:monospace;color:#475569;">{val}</span>'

    # Plain string — escape HTML entities.
    return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_table(table_data, gradient_rgb=None):
    """Render a table cell dict to a full <table> HTML string."""
    headers = table_data["headers"]
    rows    = table_data["rows"]
    n_cols  = len(headers)

    if gradient_rgb:
        r, g, b = gradient_rgb
        # Header cells fade left (full color) → right (40 % tint).
        th_cells_parts = []
        for j, h in enumerate(headers):
            t      = j / max(n_cols - 1, 1)
            factor = 0.40 * t
            tr_    = int(r + (255 - r) * factor)
            tg_    = int(g + (255 - g) * factor)
            tb_    = int(b + (255 - b) * factor)
            col_bg = f"#{tr_:02x}{tg_:02x}{tb_:02x}"
            col_fg = "#ffffff" if not _is_light(tr_, tg_, tb_) else "#111827"
            style  = (
                f"border:1.5px solid #000;background:{col_bg};padding:4px 8px;"
                f"text-align:left;font-weight:bold;white-space:nowrap;color:{col_fg};"
            )
            th_cells_parts.append(f'<th style="{style}">{h}</th>')
        th_cells = "".join(th_cells_parts)
    else:
        th_cells = "".join(f'<th style="{_TH_STYLE}">{h}</th>' for h in headers)

    thead = f"<thead><tr>{th_cells}</tr></thead>"

    tbody_rows = []
    for i, row in enumerate(rows):
        cells = list(row)
        while len(cells) < len(headers):
            cells.append({"value": None})

        td_cells_parts = []
        for j, c in enumerate(cells):
            if gradient_rgb:
                r, g, b = gradient_rgb
                # Data cells fade left (50 % tint) → right (90 % tint).
                t      = j / max(n_cols - 1, 1)
                factor = 0.50 + 0.40 * t
                col_bg = _tint(r, g, b, factor)
                td_style = f"border:1.5px solid #000;padding:4px 8px;vertical-align:top;background:{col_bg};"
            else:
                td_style = _TD_EVEN if i % 2 else _TD_ODD
            td_cells_parts.append(f'<td style="{td_style}">{_render_cell(c, gradient_rgb)}</td>')

        tbody_rows.append(f"<tr>{''.join(td_cells_parts)}</tr>")

    tbody = f"<tbody>{''.join(tbody_rows)}</tbody>"
    return f'<table style="{_TABLE_STYLE}">{thead}{tbody}</table>'


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def yaml_to_html_table(yaml_text: str, gradient_hex: str | None = None) -> str:
    """Parse *yaml_text* and return an HTML ``<table>`` string.

    * List of dicts  → wide table (one column per unique key).
    * Plain dict     → two-column key / value table.
    * Nested values  → recursively rendered as nested ``<table>`` elements.
    * gradient_hex   → optional #RRGGBB color; leftmost column gets the full
                       color and cells fade to near-white left-to-right.
    """
    text = yaml_text.strip()
    if not text:
        return "<p>No YAML data provided.</p>"

    gradient_rgb = _hex_to_rgb(gradient_hex) if gradient_hex else None
    data = yaml.safe_load(text)

    if isinstance(data, list):
        cell = _convert_array(data)
        if cell.get("is_table"):
            return _render_table(cell, gradient_rgb)
    elif isinstance(data, dict):
        cell = _convert_object(data)
        if cell.get("is_table"):
            return _render_table(cell, gradient_rgb)

    fallback = {"is_table": True, "headers": ["value"], "rows": [[{"value": data}]]}
    return _render_table(fallback, gradient_rgb)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_HTML_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>YAML to Table — {title}</title>
  <style>
    body  {{ font-family: system-ui, -apple-system, sans-serif;
             padding: 24px; background: #f3f4f6; }}
    .wrap {{ background: white; border-radius: 8px; padding: 24px;
             box-shadow: 0 1px 3px rgba(0,0,0,.12); overflow-x: auto; }}
    h1    {{ font-size: 1.1rem; color: #111827; margin: 0 0 16px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{title}</h1>
    {table}
  </div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="Convert a YAML file to an HTML table",
        epilog="Output defaults to <input>.html",
    )
    parser.add_argument("input",  help="Input YAML file")
    parser.add_argument("-o", "--output", help="Output HTML file")
    parser.add_argument(
        "--color",
        metavar="HEX",
        help="Apply a color gradient using this base hex color (e.g. #4f46e5)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: '{args.input}' not found.")

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")

    yaml_text  = input_path.read_text()
    table_html = yaml_to_html_table(yaml_text, gradient_hex=args.color)

    html = _HTML_WRAPPER.format(title=input_path.name, table=table_html)
    output_path.write_text(html)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
