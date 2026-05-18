#!/usr/bin/env python3
"""
db_cli.py — Read/write/admin command surface for the SQLite store.

Usage:
    python3 db_cli.py <command> '<json args>'
    python3 db_cli.py context '{}'
    python3 db_cli.py schema '{}'
    python3 db_cli.py recent-orders '{"limit":5,"status":"pending"}'

All commands output JSON on stdout. Errors go to stderr with a non-zero exit code.

Override the db path:
    DB_PATH=/custom/path.db python3 db_cli.py context '{}'
"""
import sys, json, sqlite3, os, pathlib, shutil, csv, io

DB_PATH = pathlib.Path(os.environ.get(
    "DB_PATH",
    os.path.expanduser("~/.local/share/myapp/store.db")
))

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        import sqlite_vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
    except ImportError:
        pass
    return conn

# ── INTEROP ───────────────────────────────────────────────────────────────

def context():
    """Self-describing entry point for other skills.
    Returns db path, table row counts, and the full command list.
    Call this first when consuming this db from another skill."""
    conn   = connect()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name != '_migrations' ORDER BY name"
    ).fetchall()
    result = {
        "db_path":  str(DB_PATH),
        "exists":   DB_PATH.exists(),
        "tables":   {},
        "commands": list(COMMANDS.keys()),
    }
    for (t,) in tables:
        try:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {t} WHERE deleted_at IS NULL"
            ).fetchone()[0]
            total = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            # table has no deleted_at column
            total = count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        result["tables"][t] = {"live_rows": count, "total_rows": total}
    conn.close()
    return result

def schema():
    """Returns the full schema as structured JSON — tables, columns, types,
    indexes, and applied migrations. Use this instead of parsing SKILL.md."""
    conn       = connect()
    tables     = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name != '_migrations' ORDER BY name"
    ).fetchall()
    indexes    = conn.execute(
        "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name, name"
    ).fetchall()
    try:
        migrations = conn.execute(
            "SELECT filename, applied_at FROM _migrations ORDER BY id"
        ).fetchall()
    except sqlite3.OperationalError:
        migrations = []
    result = {"tables": {}, "indexes": [], "migrations": []}
    for (t,) in tables:
        cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
        result["tables"][t] = [
            {
                "name":     c[1],
                "type":     c[2],
                "not_null": bool(c[3]),
                "default":  c[4],
                "pk":       bool(c[5]),
            }
            for c in cols
        ]
    result["indexes"]    = [{"name": r[0], "table": r[1], "sql": r[2]} for r in indexes]
    result["migrations"] = [{"file": r[0], "applied_at": r[1]} for r in migrations]
    conn.close()
    return result

# ── WRITES ────────────────────────────────────────────────────────────────

def insert_order(customer, total_cents, status="pending"):
    conn = connect()
    cur  = conn.execute(
        "INSERT INTO orders (customer, total_cents, status) VALUES (?,?,?)",
        (customer, total_cents, status)
    )
    conn.commit(); conn.close()
    return {"id": cur.lastrowid}

def save_template(name, payload: dict):
    conn = connect()
    conn.execute(
        """INSERT INTO templates (name, payload, updated_at)
           VALUES (?, ?, datetime('now'))
           ON CONFLICT(name) DO UPDATE SET
             payload    = excluded.payload,
             updated_at = excluded.updated_at,
             deleted_at = NULL""",
        (name, json.dumps(payload))
    )
    conn.commit(); conn.close()
    return {"saved": name}

def update_order_status(order_id, status):
    conn = connect()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit(); conn.close()
    return {"updated": order_id, "status": status}

def soft_delete(table, record_id):
    """Soft-delete a row by setting deleted_at. Never hard-deletes."""
    conn = connect()
    conn.execute(
        f"UPDATE {table} SET deleted_at = datetime('now') WHERE id = ?",
        (record_id,)
    )
    conn.commit(); conn.close()
    return {"deleted": record_id, "table": table}

def restore(table, record_id):
    """Undo a soft delete by clearing deleted_at."""
    conn = connect()
    conn.execute(
        f"UPDATE {table} SET deleted_at = NULL WHERE id = ?",
        (record_id,)
    )
    conn.commit(); conn.close()
    return {"restored": record_id, "table": table}

# ── READS ─────────────────────────────────────────────────────────────────

def get_template(name):
    conn = connect()
    row  = conn.execute(
        "SELECT * FROM templates WHERE name=? AND deleted_at IS NULL", (name,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    r = dict(row)
    r["payload"] = json.loads(r["payload"])
    return r

def recent_orders(limit=10, status=None, since=None, include_deleted=False):
    """since: ISO date string e.g. '2026-01-01' — uses created_at index."""
    conn    = connect()
    clauses, params = [], []
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if status:
        clauses.append("status = ?")
        params.append(status)
    if since:
        clauses.append("created_at >= ?")
        params.append(since)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    rows = conn.execute(
        f"SELECT * FROM orders {where} ORDER BY created_at DESC LIMIT ?", params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_order(order_id, include_deleted=False):
    conn    = connect()
    deleted = "" if include_deleted else "AND deleted_at IS NULL"
    row     = conn.execute(
        f"SELECT * FROM orders WHERE id=? {deleted}", (order_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def fts_search(query, limit=10):
    """Keyword search across FTS5-indexed columns. Returns rowids + rank."""
    conn = connect()
    rows = conn.execute(
        "SELECT rowid, rank FROM orders_fts WHERE orders_fts MATCH ? ORDER BY rank LIMIT ?",
        (query, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query(sql, params=None):
    """Ad-hoc SELECT-only escape hatch. Rejects any non-SELECT statement."""
    sql_stripped = sql.strip().upper()
    forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "DETACH")
    if not sql_stripped.startswith("SELECT") or any(kw in sql_stripped for kw in forbidden):
        raise ValueError("query() only accepts SELECT statements")
    conn = connect()
    rows = conn.execute(sql, params or []).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── BULK I/O ──────────────────────────────────────────────────────────────

def bulk_import(table, records: list, mode="insert"):
    """Import a list of dicts into a table.
    mode='insert'  — plain INSERT, fails on conflict
    mode='upsert'  — INSERT OR REPLACE
    mode='ignore'  — INSERT OR IGNORE (skip duplicates silently)
    """
    if not records:
        return {"imported": 0}
    modes = {
        "insert": "INSERT",
        "upsert": "INSERT OR REPLACE",
        "ignore": "INSERT OR IGNORE",
    }
    if mode not in modes:
        raise ValueError(f"mode must be one of {list(modes)}")
    cols         = list(records[0].keys())
    placeholders = ",".join(["?"] * len(cols))
    sql          = f"{modes[mode]} INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    conn         = connect()
    conn.executemany(sql, [[r.get(c) for c in cols] for r in records])
    conn.commit()
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return {"imported": len(records), "table_total": total}

def bulk_export(table, fmt="json", dest=None, include_deleted=False):
    """Export an entire table to JSON or CSV.
    fmt='json' → newline-delimited JSON; written to dest or returned inline
    fmt='csv'  → CSV written to dest file, or returned as string if no dest
    """
    conn    = connect()
    deleted = "" if include_deleted else "WHERE deleted_at IS NULL"
    try:
        rows = [dict(r) for r in conn.execute(
            f"SELECT * FROM {table} {deleted} ORDER BY created_at"
        ).fetchall()]
    except sqlite3.OperationalError:
        # table has no deleted_at column
        rows = [dict(r) for r in conn.execute(
            f"SELECT * FROM {table} ORDER BY rowid"
        ).fetchall()]
    conn.close()

    if fmt == "json":
        payload = "\n".join(json.dumps(r, default=str) for r in rows)
        if dest:
            pathlib.Path(dest).write_text(payload)
            return {"exported": len(rows), "file": dest}
        return rows

    elif fmt == "csv":
        if not rows:
            return {"exported": 0}
        buf = io.StringIO()
        w   = csv.DictWriter(buf, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
        if dest:
            pathlib.Path(dest).write_text(buf.getvalue())
            return {"exported": len(rows), "file": dest}
        return {"exported": len(rows), "csv": buf.getvalue()}

    raise ValueError("fmt must be 'json' or 'csv'")

def db_export(dest=None):
    """Copy the .db file itself for download or sharing.
    If present_files tool is available in the calling context, surface the result as a download."""
    out = pathlib.Path(dest) if dest else pathlib.Path.cwd() / DB_PATH.name
    shutil.copy2(DB_PATH, out)
    return {"exported_to": str(out)}

# ── DISPATCH ──────────────────────────────────────────────────────────────

COMMANDS = {
    # interop
    "context":             context,
    "schema":              schema,
    # writes
    "insert-order":        insert_order,
    "save-template":       save_template,
    "update-order-status": update_order_status,
    "soft-delete":         soft_delete,
    "restore":             restore,
    # reads
    "get-template":        get_template,
    "get-order":           get_order,
    "recent-orders":       recent_orders,
    "fts-search":          fts_search,
    "query":               query,
    # bulk
    "bulk-import":         bulk_import,
    "bulk-export":         bulk_export,
    "db-export":           db_export,
}

if __name__ == "__main__":
    cmd  = sys.argv[1] if len(sys.argv) > 1 else "help"
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    if cmd not in COMMANDS:
        print(json.dumps({"error": "unknown command", "commands": list(COMMANDS)}))
        sys.exit(2)
    try:
        result = COMMANDS[cmd](**args)
        print(json.dumps(result, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
