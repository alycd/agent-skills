#!/usr/bin/env python3
"""
init_db.py — Apply schema + pending migrations, then rewrite the Schema Reference
in SKILL.md so the agent's knowledge stays current.

Usage:
    python3 init_db.py                  # use default DB_PATH
    DB_PATH=/custom/path.db python3 init_db.py

Run this after:
  - First setup
  - Any edit to schema.sql
  - Adding a new file to migrations/
"""
import sqlite3, os, re, pathlib, json

SCHEMA_PATH    = pathlib.Path("schema.sql")
MIGRATIONS_DIR = pathlib.Path("migrations")
DB_PATH        = pathlib.Path(os.environ.get(
    "DB_PATH",
    os.path.expanduser("~/.local/share/myapp/store.db")
))
SKILL_PATH     = pathlib.Path("SKILL.md")

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

lines = [
    "## Schema Reference\n\n",
    "<!-- AUTO-GENERATED — edit schema.sql or add a migration, then run python3 init_db.py -->\n\n",
]
for (table,) in tables:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    tbl_comment = ""
    if SCHEMA_PATH.exists():
        for line in SCHEMA_PATH.read_text().splitlines():
            if re.match(rf"--\s*{table}:", line):
                tbl_comment = line.lstrip("- ").strip()
                break
    lines.append(f"### `{table}`\n")
    if tbl_comment:
        lines.append(f"_{tbl_comment}_\n\n")
    lines.append("| column | type | not null | default | notes |\n")
    lines.append("|--------|------|----------|---------|-------|\n")
    for col in cols:
        notnull = "✓" if col[3] else ""
        default = col[4] or ""
        notes   = col_comments.get(col[1], "")
        lines.append(f"| `{col[1]}` | {col[2]} | {notnull} | {default} | {notes} |\n")
    lines.append("\n")

conn.close()
new_block = "".join(lines)

# ── 7. Splice into SKILL.md ───────────────────────────────────────────────
if SKILL_PATH.exists():
    skill = SKILL_PATH.read_text()
    skill = re.sub(
        r"## Schema Reference\n.*?(?=\n---)",
        new_block.rstrip("\n"),
        skill,
        flags=re.DOTALL
    )
    SKILL_PATH.write_text(skill)
    print(f"✓ Skill updated: {SKILL_PATH}")

print(f"✓ DB ready:      {DB_PATH}")
