---
name: sqlite-db-generator
description: >
  Design and build a local SQLite database — brainstorm entities, define schemas, write records,
  query data, and expose a standard interface other skills can consume. Use this skill whenever
  the user wants to persist structured data locally, think through a data model, create or update
  a SQLite schema, insert or update records, run queries, bulk import/export data, or build a
  lightweight local store for an agent or CLI tool. Also trigger when the user edits schema.sql
  and wants the skill and db to reflect those changes. Trigger phrases: "create a sqlite db",
  "set up a local database", "store this in sqlite", "help me design a schema", "what tables
  do I need", "save records to a db", "query my local db", "update the schema", "add a table",
  "sync the schema", "export my data", "import records".
---

# SQLite Store Skill

A skill for designing and building a local SQLite database. Always start with the brainstorming
phase — rushing to tables before understanding the domain produces schemas that need to be
rewritten. The **`schema.sql` file is the single source of truth** once design is done. After any
schema change, run the sync command to keep the db and this skill in sync.

Other skills can consume this db via the standard `context` and `schema` commands — no Markdown
parsing required.

---

## File Layout

```
<project>/
├── schema.sql              ← source of truth; edit this to change the db structure
├── migrations/             ← versioned .sql files for schema changes after initial deploy
│   └── 001_initial.sql
├── scripts/
│   ├── init_db.py          ← applies schema + pending migrations, rewrites Schema Reference
│   └── db_cli.py           ← all read/write/admin commands the agent calls
└── .gitignore              ← add *.db here
```

The scripts in `scripts/` are bundled with this skill — copy them into your project as-is.
Override `DB_PATH` via environment variable or edit the default at the top of each file:
```bash
DB_PATH=/my/custom/path.db python3 scripts/init_db.py
DB_PATH=/my/custom/path.db python3 scripts/db_cli.py context '{}'
```

---

## Phase 1 — Brainstorm Before Writing SQL

**Never open a text editor until this phase is complete.** Ask the user these questions
one group at a time, waiting for answers before moving on. Use their answers to catch
design problems early — it is much cheaper to rename an entity now than to migrate data later.

### 1.1 — Goals and scope

Ask:
- What are you trying to achieve with this database? What problem does it solve?
- Who or what reads from it — a human via CLI, an agent, a web app, or all three?
- Roughly how much data do you expect — hundreds of rows, millions, or somewhere in between?
- Does this need to be shared across machines, or is local-only fine?
- Will other skills or tools need to read from this db? If so, what do they need to know about it?

*Listen for:* scale hints (affects index strategy), sharing needs (flag if they describe
multi-writer or networked access — SQLite may be the wrong choice), and interop signals
(another skill consuming this db means the `context`/`schema` commands are essential).

### 1.2 — Major entities

Ask:
- What are the main "things" your app tracks? (e.g. users, orders, products, sessions, events)
- For each thing: what's the natural identifier — a name people type, an auto-generated ID, or
  something from an external system (like an order number from an API)?
- Are any of these things hierarchical? (e.g. "a cart has items")

*From their answers, draft a plain-English entity list like:*
```
Entities identified:
- Order       — one per placed order; identified by auto-increment ID
- Template    — named reusable config; identified by a human-chosen name
- OrderItem   — child of Order; one row per line item
```

Show this to the user and confirm before continuing.

### 1.3 — Relationships

Ask:
- Which entities belong to other entities? (one order has many items, one user has many orders)
- Can something belong to multiple parents? (a product can be in many orders — many-to-many)
- When a parent is deleted, what should happen to its children?
  - Cascade delete (children disappear too)?
  - Restrict (block the delete if children exist)?
  - Set null (children become orphaned but stay)?

*Map this to foreign keys:*
```
OrderItem.order_id → Order.id   ON DELETE CASCADE
```

Flag many-to-many relationships early — they need a join table and the user may not realize it.

### 1.4 — Column special cases

For each entity, ask:

**Full-text search**
- Do users need to search this entity by keyword? (e.g. "find orders mentioning pepperoni")
- If yes → plan an FTS5 virtual table + sync trigger for that entity (see Column Patterns below).

**JSON / flexible payloads**
- Are there fields where the shape varies per row, or you don't know all the keys yet?
- If yes → `TEXT` column storing JSON. Name it `payload`, `metadata`, or `config` (not `data` —
  too vague). Always note in the comment what keys you expect: `-- JSON: {store_id, items[], note}`.

**Enumerations**
- Are there status or type fields with a fixed set of values?
- If yes → `TEXT` with a `CHECK` constraint: `CHECK(status IN ('pending','active','done'))`.
  Don't use integers for enums in SQLite — unreadable in queries.

**Vectors**
- Do you need semantic similarity search (find records "like" this one)?
- If yes → plan a `vec0` virtual table via `sqlite-vec`. Requires `pip install sqlite-vec` and
  storing embeddings separately from the main table (see Column Patterns below).

**Soft deletes**
- Will any other skill or tool need to see historical records even after they're "removed"?
- Will you need an audit trail or undo capability?
- If yes (or if unsure) → add `deleted_at TEXT DEFAULT NULL` to the table. Rows are never
  hard-deleted; instead `UPDATE t SET deleted_at = datetime('now') WHERE id = ?`. All read
  commands filter `WHERE deleted_at IS NULL` by default; pass `include_deleted=true` to see all.

### 1.5 — Query patterns

Ask:
- What are the three most common queries you'll run?
  (e.g. "get all pending orders", "find a template by name", "order history for a customer")
- Do you need to filter or sort by date often?
- Do you need to look things up by a non-primary-key field frequently?
  (e.g. "find order by phone number" — that column needs an index)
- Will you ever need to run ad-hoc queries not covered by named commands?
  (if yes → the `query` escape hatch in db_cli.py handles this safely)

*Use answers to plan indexes beyond the primary key.*

### 1.6 — Storage location

Ask:
- Where do you want the `.db` file to live? Options:
  1. **Project-local** — `./<projectname>.db` next to your code. Travels with the repo, easy to
     find, easy to delete. Add to `.gitignore` if it contains real data.
  2. **User data directory** — `~/.local/share/<appname>/store.db` (Linux/macOS). Survives
     project moves; good for persistent user state like a CLI tool's history.
  3. **Temp / scratch** — `/tmp/<name>.db`. Wiped on reboot; good for throwaway experiments.
  4. **Download** — generate the `.db` file and offer it as a download. Good for one-off exports
     or sandboxed environments where filesystem navigation is awkward.
  5. **Custom path** — user specifies an exact path.

*Set `DB_PATH` in both `init_db.py` and `db_cli.py` before generating any code.*

**Flag if they say:** "share it", "send it to me", "export it", "download it" — all mean option 4.

**Download support (add to db_cli.py when chosen):**
```python
def db_export(dest=None):
    import shutil
    out = pathlib.Path(dest) if dest else pathlib.Path.cwd() / DB_PATH.name
    shutil.copy2(DB_PATH, out)
    # If present_files tool is available, call it here to surface a download link
    return {"exported_to": str(out)}
```

### 1.7 — Design confirmation

Before writing any SQL, present a summary:

```
Proposed design:
  Tables:       orders, order_items, templates
  Soft deletes: orders (deleted_at column)
  FTS:          orders_fts (on customer, item fields)
  Indexes:      orders(status), orders(created_at), order_items(order_id)
  JSON cols:    templates.payload {store_id, items[], payment_ref}
  Enums:        orders.status IN ('pending','confirmed','delivered','cancelled')
  DB path:      ./myapp.db  (project-local, added to .gitignore)
  Migrations:   migrations/ folder, versioned from 001

Questions / flags:
  - order_items is a new table not mentioned initially — confirm this is right
  - Soft deletes on orders only; order_items cascade-delete so no need there
  - No vector search planned; add later if needed
```

Get explicit confirmation before moving to Phase 2.

---

## Phase 2 — Write schema.sql

With the design confirmed, translate it into SQL. Follow all rules below.

### Mandatory columns on every table

```sql
created_at  TEXT NOT NULL DEFAULT (datetime('now')),  -- set once on insert, never updated
updated_at  TEXT NOT NULL DEFAULT (datetime('now')),  -- updated via trigger on every UPDATE
deleted_at  TEXT DEFAULT NULL                         -- NULL = live; timestamp = soft-deleted
```

Always add `updated_at` and soft-delete triggers for every table:

```sql
CREATE TRIGGER orders_updated_at
AFTER UPDATE ON orders
BEGIN
    UPDATE orders SET updated_at = datetime('now') WHERE id = NEW.id;
END;
```

### Column patterns

**Standard row (append-only records):**
```sql
CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    deleted_at   TEXT    DEFAULT NULL,                         -- soft delete
    customer     TEXT    NOT NULL,                             -- display name or user ID
    status       TEXT    NOT NULL DEFAULT 'pending'
                         CHECK(status IN ('pending','confirmed','delivered','cancelled')),
    total_cents  INTEGER NOT NULL                              -- price in cents, never floats
);
```

**Named/keyed resource (upsertable):**
```sql
CREATE TABLE IF NOT EXISTS templates (
    name         TEXT PRIMARY KEY,                         -- human key, e.g. "friday-night"
    payload      TEXT NOT NULL,                            -- JSON: {store_id, items[], payment_ref}
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at   TEXT DEFAULT NULL
);
```

**Child table (foreign key):**
```sql
CREATE TABLE IF NOT EXISTS order_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    product_code TEXT    NOT NULL,                         -- e.g. "S_PIZPH"
    quantity     INTEGER NOT NULL DEFAULT 1,
    unit_cents   INTEGER NOT NULL
);
```

**Full-text search (FTS5 virtual table + sync triggers):**
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS orders_fts USING fts5(
    customer,
    product_code,
    content='orders',
    content_rowid='id'
);

CREATE TRIGGER orders_fts_ai AFTER INSERT ON orders BEGIN
    INSERT INTO orders_fts(rowid, customer, product_code)
    VALUES (new.id, new.customer, new.product_code);
END;

CREATE TRIGGER orders_fts_ad AFTER DELETE ON orders BEGIN
    INSERT INTO orders_fts(orders_fts, rowid, customer, product_code)
    VALUES ('delete', old.id, old.customer, old.product_code);
END;
```

**Vector search (sqlite-vec, installed separately):**
```sql
-- Requires: pip install sqlite-vec
CREATE VIRTUAL TABLE IF NOT EXISTS order_embeddings USING vec0(
    id      INTEGER PRIMARY KEY,
    vector  FLOAT[1536]
);
```

### Index patterns

```sql
CREATE INDEX IF NOT EXISTS idx_orders_created_at   ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_updated_at   ON orders(updated_at);
CREATE INDEX IF NOT EXISTS idx_orders_deleted_at   ON orders(deleted_at);   -- fast live-row filter
CREATE INDEX IF NOT EXISTS idx_orders_status       ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_status_date  ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order   ON order_items(order_id);
```

Rule of thumb: if a query filters or sorts by a column more than occasionally, it needs an index.
`deleted_at` always gets an index — nearly every query filters on it.

---

## Phase 3 — Migrations

Schema changes after the initial deploy go in `migrations/`, not back into `schema.sql` directly.
This preserves history and lets `init_db.py` apply only the deltas that haven't run yet.

### Migration file naming

```
migrations/
  001_initial.sql       ← copy of the original schema.sql at deploy time
  002_add_phone.sql     ← ALTER TABLE orders ADD COLUMN phone TEXT;
  003_add_notes.sql     ← ALTER TABLE orders ADD COLUMN notes TEXT DEFAULT '';
```

Each file is append-only — never edit a migration that has already run.

### Running the sync

```bash
python3 scripts/init_db.py
```

This does three things in one shot:
1. Creates the `_migrations` tracking table if it doesn't exist.
2. Applies `schema.sql` (first run only) or any pending `migrations/*.sql` files.
3. Rewrites the **Schema Reference** section of this `SKILL.md` with the live column structure.

See `scripts/init_db.py` for the full implementation — it is the bundled source of truth.



---

## Phase 4 — db_cli.py

The full command surface lives in `scripts/db_cli.py` — bundled with this skill. Other skills
call it as a subprocess and parse the JSON output. Every command outputs JSON on stdout;
errors go to stderr with a non-zero exit code.

**Agent call examples:**
```bash
python3 scripts/db_cli.py context '{}'
python3 scripts/db_cli.py schema '{}'
python3 scripts/db_cli.py insert-order '{"customer":"aly","total_cents":1299}'
python3 scripts/db_cli.py recent-orders '{"limit":5,"status":"pending","since":"2026-01-01"}'
python3 scripts/db_cli.py fts-search '{"query":"pepperoni","limit":5}'
python3 scripts/db_cli.py save-template '{"name":"friday-night","payload":{"store":7144}}'
python3 scripts/db_cli.py get-template '{"name":"friday-night"}'
python3 scripts/db_cli.py update-order-status '{"order_id":3,"status":"delivered"}'
python3 scripts/db_cli.py soft-delete '{"table":"orders","record_id":3}'
python3 scripts/db_cli.py restore '{"table":"orders","record_id":3}'
python3 scripts/db_cli.py query '{"sql":"SELECT * FROM orders WHERE status = ?","params":["pending"]}'
python3 scripts/db_cli.py bulk-import '{"table":"orders","records":[...],"mode":"upsert"}'
python3 scripts/db_cli.py bulk-export '{"table":"orders","fmt":"csv","dest":"orders.csv"}'
python3 scripts/db_cli.py db-export '{}'
```

---

## Command Reference

### Interop commands (for other skills)

| Command | Args | Returns |
|---------|------|---------|
| `context` | — | `{db_path, exists, tables: {name: {live_rows, total_rows}}, commands[]}` |
| `schema` | — | `{tables: {name: [{name,type,not_null,default,pk}]}, indexes[], migrations[]}` |

**How another skill consumes this db:**
```bash
# 1. Discover what's here
python3 db_cli.py context '{}'

# 2. Get full column detail for a specific table
python3 db_cli.py schema '{}' | python3 -c "import sys,json; s=json.load(sys.stdin); print(json.dumps(s['tables']['orders'], indent=2))"

# 3. Run a targeted read
python3 db_cli.py recent-orders '{"limit":10,"status":"pending"}'
```

### Write commands

| Command | Key args | Notes |
|---------|----------|-------|
| `insert-order` | `customer`, `total_cents` | Returns `{id}` |
| `save-template` | `name`, `payload` (dict) | Upsert; restores if soft-deleted |
| `update-order-status` | `order_id`, `status` | |
| `soft-delete` | `table`, `record_id` | Sets `deleted_at`; never hard-deletes |
| `restore` | `table`, `record_id` | Clears `deleted_at` |

### Read commands

| Command | Key args | Notes |
|---------|----------|-------|
| `get-order` | `order_id` | Pass `include_deleted=true` to see soft-deleted |
| `get-template` | `name` | Returns null if not found or soft-deleted |
| `recent-orders` | `limit`, `status`, `since`, `include_deleted` | `since` uses index |
| `fts-search` | `query`, `limit` | Returns `[{rowid, rank}]` |
| `query` | `sql`, `params` | SELECT only; raises on any write keyword |

### Bulk commands

| Command | Key args | Notes |
|---------|----------|-------|
| `bulk-import` | `table`, `records` (list), `mode` | `insert` / `upsert` / `ignore` |
| `bulk-export` | `table`, `fmt`, `dest` | `json` or `csv`; omit `dest` for inline |
| `db-export` | `dest` | Copies the `.db` file itself |

---

## Schema Reference

<!-- AUTO-GENERATED — edit schema.sql or add a migration, then run python3 init_db.py -->

_Run `python3 init_db.py` once to populate this section with your live schema._

---

## DB Path Convention

| Option | Path | When to use |
|--------|------|-------------|
| Project-local | `./<projectname>.db` | Code and db travel together. Add to `.gitignore`. |
| User data dir | `~/.local/share/<appname>/store.db` | Persistent user state; survives project moves. |
| Temp/scratch | `/tmp/<name>.db` | Throwaway experiments. Wiped on reboot. |
| Download | current dir + `present_files` | One-off export or sandboxed environments. |
| Custom | user-specified path | Anything else. |

`DB_PATH` is set once in both `init_db.py` and `db_cli.py` — change it in one place during
Phase 1 so it never drifts between the two files.

---

## The Sync Loop

```
Edit schema.sql  (or add migrations/<N>_change.sql for existing dbs)
      ↓
python3 init_db.py
      ↓
db file updated  +  Schema Reference in this SKILL.md rewritten
      ↓
Agent reads updated skill → knows exactly what tables/columns/indexes exist
      ↓
Other skills call: python3 db_cli.py context '{}'  →  self-describing JSON entry point
```

No manual skill edits. No schema inspection at runtime. One command keeps everything in sync.
