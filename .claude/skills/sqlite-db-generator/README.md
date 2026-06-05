# sqlite-db-generator

A Claude Code skill for designing and building local SQLite databases. Guides you through
brainstorming entities and relationships, writes the schema, generates scripts, and produces
a dedicated agent skill for the new DB — all kept in sync by a single command.

---

## What it produces

Running the skill and then `python3 scripts/init_db.py` gives you:

```
<project>/
├── schema.sql                        ← source of truth; edit to change structure
├── migrations/                       ← versioned deltas after initial deploy
│   └── 001_initial.sql
├── scripts/
│   └── init_db.py                    ← bootstrap + sync; run after every schema change
├── db/
│   └── <name>.db                     ← DB file (add to .gitignore)
└── .claude/
    └── skills/
        └── <name>-db/
            ├── SKILL.md              ← auto-generated agent skill
            └── db_cli.py             ← CLI with absolute DB_PATH baked in
```

---

## Scope: local vs global

Set `DB_SCOPE` at the top of `scripts/init_db.py` before first run.

### Local (default)

```
DB_SCOPE = "local"
```

| | Path |
|---|---|
| DB | `./db/<name>.db` — inside the project folder |
| Skill | `./.claude/skills/<name>-db/` — visible only when this project is open |

Use when the DB belongs to a specific codebase. Travels with the repo.

### Global

```
DB_SCOPE = "global"
```

| | Path |
|---|---|
| DB | `~/db/<name>.db` — stable home-directory path |
| Skill | `~/.claude/skills/<name>-db/` — visible from every project |

Use for personal tools you want accessible everywhere: second brain, bug tracker, link vault.

> Either way, `db_cli.py` in the skill folder has the absolute DB path baked in and can be
> called from any working directory.

---

## Sync loop

```
Edit schema.sql  (or add migrations/NNN_change.sql)
        ↓
python3 scripts/init_db.py
        ↓
  db/<name>.db updated
  .claude/skills/<name>-db/SKILL.md   ← Schema Reference section spliced
  .claude/skills/<name>-db/db_cli.py  ← re-copied with absolute DB_PATH
```

One command keeps the DB, the CLI, and the agent skill in sync. No manual edits needed.

---

## Webapp access

Webapps connect directly to the DB file — no API layer required:

```python
# Python
import sqlite3
conn = sqlite3.connect("/abs/path/to/db/<name>.db")
```

```js
// Node — better-sqlite3
const Database = require('better-sqlite3')
const db = new Database('/abs/path/to/db/<name>.db')
```

```ts
// Bun + Drizzle
import { drizzle } from 'drizzle-orm/bun-sqlite'
import { Database } from 'bun:sqlite'
const db = drizzle(new Database('/abs/path/to/db/<name>.db'))
```

The generated skill documents the exact path after first run.

---

## How other skills consume the DB

Other skills call `db_cli.py` directly — no need to load the `<name>-db` skill:

```bash
# Discover what's available
python3 .claude/skills/<name>-db/db_cli.py context '{}'

# Query
python3 .claude/skills/<name>-db/db_cli.py fts-search '{"query":"keyword","limit":10}'
```

`context` returns self-describing JSON `{db_path, tables, commands[]}` — the standard
interop entry point for any consumer.

---

## Entity names in the generated skill

The skill description is auto-derived from the first table name using naive singularization
(`bugs → bug`, `orders → order`). If the result looks wrong (irregular plurals, etc.),
edit the `description` field in `.claude/skills/<name>-db/SKILL.md` — re-running
`init_db.py` only updates the Schema Reference section, not the frontmatter.

---

## Scaffolding decisions

These are the key design choices baked into the generator and why.

### Scripts live in the skill folder, not the project

`db_cli.py` is copied into `.claude/skills/<name>-db/` with an absolute `DB_PATH` baked
in. This means the agent can call it from any working directory — not just the project
it was created in. The source template lives in `scripts/` during development; the copy
in the skill folder is what the agent actually uses.

`init_db.py` stays in `scripts/` — it's a setup and migration tool run manually, not
something the agent calls on every query.

### DB lives in `db/` not the project root

A dedicated `db/` folder separates data from code, makes `.gitignore` entries obvious
(`db/*.db`), and gives webapps a predictable stable path to connect to without knowing
anything about the skill or CLI.

### Webapps connect directly to the file

SQLite is a file DB. There's no reason to put an HTTP API in front of it for local use —
any process on the same machine can open the `.db` file with its own driver. The generated
skill documents Python, Node, and Bun snippets so any stack can connect without looking
anything up.

### Skill description uses naive singularization, not db_meta.json

An earlier design proposed storing entity metadata in `db_meta.json` and asking for it
during brainstorming. This was dropped in favour of auto-deriving from the first table
name and leaving a comment in the frontmatter. The description is only written once and
never overwritten — so a one-time manual edit is cheap and avoids an extra file and an
extra question.

### Schema Reference is the only auto-updated section

On first run, `init_db.py` writes the full `SKILL.md`. On subsequent runs (after
migrations), it splices only the `## Schema Reference` section via regex. Everything
else — description, commands, webapp snippets — is stable and safe to hand-edit.

### local vs global scope is a single variable

Rather than asking multiple questions about paths, the generator exposes one
`DB_SCOPE` variable (`local` / `global`) that sets both the DB path and the skill
location consistently. Power users can still override `DB_PATH` directly via env var
for non-standard layouts.
