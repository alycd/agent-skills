#!/usr/bin/env python3
"""
init_db.py — Apply schema + pending migrations, then regenerate:
  - db/{name}.db                              (project-local, default)
  - ~/db/{name}.db                            (global, DB_SCOPE=global)
  - .claude/skills/{name}-db/SKILL.md         ← auto-generated agent skill
  - .claude/skills/{name}-db/db_cli.py        ← absolute DB_PATH baked in

Usage:
    python3 scripts/init_db.py
    DB_SCOPE=global python3 scripts/init_db.py
    DB_NAME=myapp python3 scripts/init_db.py
    DB_PATH=/custom/path.db python3 scripts/init_db.py

Re-run after: first setup, any edit to schema.sql, any new migrations/*.sql file.
"""
import sqlite3, os, re, pathlib, json, shutil

# ── Config ────────────────────────────────────────────────────────────────
DB_SCOPE = os.environ.get("DB_SCOPE", "local")     # "local" | "global"
DB_NAME  = os.environ.get("DB_NAME",  pathlib.Path.cwd().name)

_db_default = (
    pathlib.Path.home() / "db" / f"{DB_NAME}.db"
    if DB_SCOPE == "global"
    else pathlib.Path("db") / f"{DB_NAME}.db"
)
DB_PATH        = pathlib.Path(os.environ.get("DB_PATH", str(_db_default)))
SCHEMA_PATH    = pathlib.Path("schema.sql")
MIGRATIONS_DIR = pathlib.Path("migrations")
CLAUDE_PATH    = pathlib.Path("CLAUDE.md")

SKILL_NAME = DB_PATH.stem + "-db"
SKILL_DIR  = (
    pathlib.Path.home() / ".claude" / "skills" / SKILL_NAME
    if DB_SCOPE == "global"
    else pathlib.Path(".claude") / "skills" / SKILL_NAME
)

# ── 1. Connect ────────────────────────────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
try:
    import sqlite_vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    print("✓ sqlite-vec loaded")
except ImportError:
    pass

# ── 2. Bootstrap migration tracking ──────────────────────────────────────
conn.execute("""
    CREATE TABLE IF NOT EXISTS _migrations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        filename    TEXT    NOT NULL UNIQUE,
        applied_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    )
""")
conn.commit()

# ── 3. Apply schema.sql on first run ─────────────────────────────────────
applied = {r["filename"] for r in conn.execute("SELECT filename FROM _migrations").fetchall()}
if not applied and SCHEMA_PATH.exists():
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute("INSERT INTO _migrations (filename) VALUES (?)", ("schema.sql",))
    conn.commit()
    print("✓ Applied schema.sql")

# ── 4. Apply pending migrations in order ─────────────────────────────────
if MIGRATIONS_DIR.exists():
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if f.name not in applied:
            conn.executescript(f.read_text())
            conn.execute("INSERT INTO _migrations (filename) VALUES (?)", (f.name,))
            conn.commit()
            print(f"✓ Applied migration: {f.name}")

# ── 5. Read column comments from schema.sql ───────────────────────────────
col_comments = {}
if SCHEMA_PATH.exists():
    for line in SCHEMA_PATH.read_text().splitlines():
        m = re.match(r"\s+(\w+)\s+\w.*--\s*(.+)", line)
        if m:
            col_comments[m.group(1).strip()] = m.group(2).strip()

# ── 6. Build Schema Reference block ──────────────────────────────────────
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE '%_fts%' AND name NOT LIKE 'sqlite_%' "
    "AND name != '_migrations' ORDER BY name"
).fetchall()

schema_lines = [
    "## Schema Reference\n\n",
    "<!-- AUTO-GENERATED — edit schema.sql or add a migration, then run python3 scripts/init_db.py -->\n\n",
]
for (table,) in tables:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    tbl_comment = ""
    if SCHEMA_PATH.exists():
        for line in SCHEMA_PATH.read_text().splitlines():
            if re.match(rf"--\s*{table}:", line):
                tbl_comment = line.lstrip("- ").strip()
                break
    schema_lines.append(f"### `{table}`\n")
    if tbl_comment:
        schema_lines.append(f"_{tbl_comment}_\n\n")
    schema_lines.append("| column | type | not null | default | notes |\n")
    schema_lines.append("|--------|------|----------|---------|-------|\n")
    for col in cols:
        notnull = "✓" if col[3] else ""
        default = col[4] or ""
        notes   = col_comments.get(col[1], "")
        schema_lines.append(f"| `{col[1]}` | {col[2]} | {notnull} | {default} | {notes} |\n")
    schema_lines.append("\n")

conn.close()
new_schema_block = "".join(schema_lines)

# ── 7. Regenerate CLAUDE.md tables section (if present) ──────────────────
if CLAUDE_PATH.exists():
    conn2 = sqlite3.connect(DB_PATH)
    conn2.row_factory = sqlite3.Row
    real_tables = conn2.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE '%_fts%' AND name NOT LIKE 'sqlite_%' "
        "AND name != '_migrations' ORDER BY name"
    ).fetchall()
    table_lines = [
        "## Tables\n\n",
        "<!-- AUTO-GENERATED — run python3 scripts/init_db.py to refresh -->\n\n",
    ]
    for (table,) in real_tables:
        cols = conn2.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = ", ".join(
            f"`{c[1]}`" for c in cols
            if c[1] not in ("created_at", "updated_at", "deleted_at")
        )
        table_lines.append(f"- **`{table}`** — {col_names}\n")
    conn2.close()
    claude = CLAUDE_PATH.read_text()
    claude = re.sub(
        r"## Tables\n.*?(?=\n## )",
        "".join(table_lines),
        claude,
        flags=re.DOTALL
    )
    CLAUDE_PATH.write_text(claude)
    print(f"✓ CLAUDE.md updated: {CLAUDE_PATH}")

# ── 8. Generate / sync the db-specific skill ─────────────────────────────
SKILL_DIR.mkdir(parents=True, exist_ok=True)
_skill_md  = SKILL_DIR / "SKILL.md"
_skill_cli = SKILL_DIR / "db_cli.py"

# Derive main entity names from first real table
_real_table_names = [t[0] for t in tables]
_main_table    = _real_table_names[0] if _real_table_names else DB_NAME
_main_singular = _main_table.rstrip("s")   # naive — Claude should override if irregular
_db_path_abs   = str(DB_PATH.resolve())
_cli_ref       = str(_skill_cli.resolve())

# 8a. Write db_cli.py into skill folder with absolute DB_PATH baked in
_src_cli = pathlib.Path(__file__).parent / "db_cli.py"
if _src_cli.exists():
    cli_src = _src_cli.read_text()
    # Replace the sentinel-marked DB_PATH block with a single hardcoded line
    cli_src = re.sub(
        r"# <<DB_PATH_START>>.*?# <<DB_PATH_END>>",
        f'DB_PATH = pathlib.Path("{_db_path_abs}")',
        cli_src,
        flags=re.DOTALL
    )
    _skill_cli.write_text(cli_src)
    _skill_cli.chmod(0o755)
    print(f"✓ Skill CLI:       {_skill_cli}")

# 8b. Build commands block using absolute CLI path
def _commands_block():
    c = _cli_ref
    t = _main_table
    s = _main_singular
    return f"""\
## Commands

```bash
# Interop
python3 {c} context '{{}}'
python3 {c} schema '{{}}'

# Reads
python3 {c} get-{s} '{{"id":1}}'
python3 {c} list-{t} '{{"limit":20}}'
python3 {c} fts-search '{{"query":"keyword","limit":10}}'
python3 {c} query '{{"sql":"SELECT * FROM {t} WHERE status = ?","params":["active"]}}'

# Writes
python3 {c} insert-{s} '{{"title":"..."}}'
python3 {c} update-{s} '{{"id":1,"status":"done"}}'
python3 {c} soft-delete '{{"table":"{t}","record_id":1}}'
python3 {c} restore '{{"table":"{t}","record_id":1}}'

# Bulk
python3 {c} bulk-export '{{"table":"{t}","fmt":"json"}}'
python3 {c} bulk-import '{{"table":"{t}","records":[...],"mode":"upsert"}}'
```"""

# 8c. Write SKILL.md (first run) or splice schema block (subsequent runs)
if not _skill_md.exists():
    skill_content = f"""\
---
name: {SKILL_NAME}
description: >
  Manage the {DB_NAME} SQLite database. Use when inserting, querying, updating,
  or searching {_main_table} in {DB_NAME}.db. Trigger phrases: "add a {_main_singular}",
  "list {_main_table}", "update {_main_singular}", "delete {_main_singular}",
  "search {DB_NAME}", "show {_main_table}", "query {DB_NAME} db".
# Entity names above were auto-derived from the first table name.
# If they look wrong (irregular plurals etc.), edit the description —
# re-running init_db.py only updates Schema Reference, not this frontmatter.
---

# {DB_NAME.title()} Database

<!-- AUTO-GENERATED by scripts/init_db.py — re-run after any schema change -->

DB:  `{_db_path_abs}`
CLI: `python3 {_cli_ref}`

## Quick Start

```bash
python3 {_cli_ref} context '{{}}'
python3 {_cli_ref} fts-search '{{"query":"keyword","limit":10}}'
```

---

{new_schema_block.rstrip()}

---

{_commands_block()}

---

## Webapp Access

Connect any SQLite driver directly to the DB file — no API layer needed:

```python
# Python
import sqlite3
conn = sqlite3.connect("{_db_path_abs}")
```

```js
// Node — better-sqlite3
const Database = require('better-sqlite3')
const db = new Database('{_db_path_abs}')
```

```ts
// Bun / Drizzle
import {{ drizzle }} from 'drizzle-orm/bun-sqlite'
import {{ Database }} from 'bun:sqlite'
const db = drizzle(new Database('{_db_path_abs}'))
```

---

## Adding a Migration

```bash
# 1. Create migrations/NNN_description.sql with your ALTER TABLE statement
# 2. python3 scripts/init_db.py   ← applies it + resyncs this skill file
```
"""
    _skill_md.write_text(skill_content)
    print(f"✓ Generated skill: {_skill_md}")
else:
    content = _skill_md.read_text()
    content = re.sub(
        r"## Schema Reference\n.*?(?=\n---)",
        new_schema_block.rstrip("\n"),
        content,
        flags=re.DOTALL
    )
    _skill_md.write_text(content)
    print(f"✓ Skill synced:    {_skill_md}")

print(f"✓ DB ready:        {_db_path_abs}")
