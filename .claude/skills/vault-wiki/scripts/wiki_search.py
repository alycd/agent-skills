#!/usr/bin/env python3
"""Local BM25 search over the vault wiki (SQLite FTS5, stdlib only, no network).

Usage:
  wiki_search.py "question or key terms" [-k 8] [--per-page 2] [--json]
  wiki_search.py --index-only          # sync the index, print stats
  wiki_search.py --rebuild "query"     # drop and rebuild the index first

The index lives in wiki/.search/index.sqlite and syncs on every run: only pages whose
mtime/hash changed are re-chunked. Ranking is BM25 with column weights
(title 2, heading 4, tags/aliases 3, body 1), porter stemming, prefix matching, and
query expansion from the ## Aliases table in wiki/index.md.
"""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

MANAGED_DIRS = ["sources", "entities", "concepts", "syntheses"]
MANAGED_FILES = ["overview.md"]
MAX_CHUNK_LINES = 80
MIN_CHUNK_CHARS = 25
STOPWORDS = set("""a an and are as at be by can do does for from has have how i in is it its
of on or says say should tell that the their there this to us was we what when where which who
why will with about did our you your me my any all into than then them these those""".split())

# ---------- paths ----------

def default_wiki():
    # scripts/ -> vault-wiki -> skills -> .claude -> vault root
    return Path(__file__).resolve().parents[4] / "wiki"


def managed_pages(wiki):
    for d in MANAGED_DIRS:
        p = wiki / d
        if p.is_dir():
            yield from sorted(p.rglob("*.md"))
    for f in MANAGED_FILES:
        if (wiki / f).is_file():
            yield wiki / f


# ---------- parsing ----------

def parse_frontmatter(lines):
    """Return (dict, index of first body line)."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            return meta, i + 1
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            else:
                val = val.strip("'\"")
            meta[key] = val
    return {}, 0


def as_list(v):
    if isinstance(v, list):
        return v
    return [v] if v else []


def chunk_page(path, wiki):
    """Split a page into heading-delimited chunks with 1-based line ranges."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    meta, body_start = parse_frontmatter(lines)
    rel = path.relative_to(wiki).as_posix()
    title = meta.get("title") or path.stem
    tags = " ".join(as_list(meta.get("tags")) + as_list(meta.get("aliases")))
    chunks, cur_head, cur_start, buf = [], "", body_start + 1, []

    def flush(end_line):
        body = "\n".join(l for l in buf if not re.match(r"^#{1,6}\s", l)).strip()
        if len(body) < MIN_CHUNK_CHARS:  # skip empty/trivial sections ("None identified.")
            return
        # split oversized sections into fixed windows so line ranges stay readable
        for off in range(0, len(buf), MAX_CHUNK_LINES):
            part = buf[off:off + MAX_CHUNK_LINES]
            if "\n".join(part).strip():
                s = cur_start + off
                chunks.append({"path": rel, "title": title, "heading": cur_head, "tags": tags,
                               "body": "\n".join(part), "start": s, "end": s + len(part) - 1})

    for i in range(body_start, len(lines)):
        line = lines[i]
        if re.match(r"^#{1,6}\s", line):
            flush(i)
            cur_head, cur_start, buf = line.lstrip("#").strip(), i + 1, [line]
        else:
            buf.append(line)
    flush(len(lines))
    # page-level fields only on the first chunk, so short sections don't all win on a tag match
    for c in chunks[1:]:
        c["title"], c["tags"] = "", ""
    return meta, title, chunks, hashlib.sha256(text.encode()).hexdigest()


def load_aliases(wiki):
    """Alias groups from the ## Aliases table in wiki/index.md."""
    idx = wiki / "index.md"
    if not idx.is_file():
        return []
    groups, in_section = [], False
    for line in idx.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## aliases"
            continue
        if not in_section or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: ") or cells[0].lower() == "name":
            continue
        names = [cells[0]] + [n.strip() for n in cells[1].split(",")]
        groups.append([n for n in names if n])
    return groups


# ---------- index ----------

SCHEMA = """
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, mtime REAL, sha TEXT, title TEXT, type TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
  title, heading, tags, body, path UNINDEXED, start UNINDEXED, end UNINDEXED,
  tokenize='porter unicode61');
"""


def open_db(wiki, rebuild=False):
    d = wiki / ".search"
    d.mkdir(exist_ok=True)
    db_path = d / "index.sqlite"
    if rebuild and db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    return db


def drop_file(db, rel):
    db.execute("DELETE FROM chunks WHERE path=?", (rel,))
    db.execute("DELETE FROM files WHERE path=?", (rel,))


def sync_index(db, wiki):
    """Re-index changed pages. Returns (changed, removed)."""
    known = {r[0]: (r[1], r[2]) for r in db.execute("SELECT path, mtime, sha FROM files")}
    seen, changed = set(), 0
    for path in managed_pages(wiki):
        rel = path.relative_to(wiki).as_posix()
        seen.add(rel)
        mtime = path.stat().st_mtime
        if rel in known and known[rel][0] == mtime:
            continue
        meta, title, chunks, sha = chunk_page(path, wiki)
        if rel in known and known[rel][1] == sha:
            db.execute("UPDATE files SET mtime=? WHERE path=?", (mtime, rel))
            continue
        drop_file(db, rel)
        db.execute("INSERT INTO files VALUES (?,?,?,?,?)",
                   (rel, mtime, sha, title, meta.get("type", "")))
        db.executemany(
            "INSERT INTO chunks(title, heading, tags, body, path, start, end) VALUES (?,?,?,?,?,?,?)",
            [(c["title"], c["heading"], c["tags"], c["body"], c["path"], c["start"], c["end"])
             for c in chunks])
        changed += 1
    removed = [p for p in known if p not in seen]
    for rel in removed:
        drop_file(db, rel)
    db.commit()
    return changed, len(removed)


# ---------- BM25 ----------

def query_terms(query, alias_groups):
    """Return (single terms, phrases) after stopword removal and alias expansion."""
    q = query.lower()
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9._-]*", q) if w not in STOPWORDS]
    words = [w.strip("._-") for w in words if len(w.strip("._-")) >= 2]
    phrases = []
    for group in alias_groups:
        lowered = [g.lower() for g in group]
        if any(re.search(r"(?<![a-z0-9])" + re.escape(g) + r"(?![a-z0-9])", q) for g in lowered):
            for g in lowered:
                (phrases if " " in g else words).append(g)
    return list(dict.fromkeys(words)), list(dict.fromkeys(phrases))


def fts_query(words, phrases):
    def quote(s):
        return '"' + s.replace('"', '""') + '"'
    parts = [quote(w) + ("*" if len(w) >= 3 else "") for w in words]
    parts += [quote(p) for p in phrases]
    return " OR ".join(parts)


def bm25_rank(db, match, limit):
    if not match:
        return []
    # column weights: title, heading, tags, body
    sql = ("SELECT rowid, bm25(chunks, 2.0, 4.0, 3.0, 1.0) AS s FROM chunks "
           "WHERE chunks MATCH ? ORDER BY s LIMIT ?")
    try:
        return db.execute(sql, (match, limit)).fetchall()
    except sqlite3.OperationalError:
        return []


# ---------- search ----------

def snippet(body, words, phrases, width=180):
    keys = phrases + [w[:5] for w in words]
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
    for line in lines:
        low = line.lower()
        if any(k in low for k in keys):
            return line[:width] + ("…" if len(line) > width else "")
    return (lines[0][:width] + "…") if lines else ""


def search(db, wiki, query, k, per_page):
    words, phrases = query_terms(query, load_aliases(wiki))
    ranked = bm25_rank(db, fts_query(words, phrases), max(k * per_page * 3, 50))
    results, per = [], {}
    for rid, score in ranked:
        path, heading, start, end, body = db.execute(
            "SELECT path, heading, start, end, body FROM chunks WHERE rowid=?", (rid,)).fetchone()
        if per.get(path, 0) >= per_page:
            continue
        per[path] = per.get(path, 0) + 1
        results.append({"path": path, "lines": [int(start), int(end)], "heading": heading,
                        "score": round(-score, 2), "snippet": snippet(body, words, phrases)})
        if len(results) >= k:
            break
    return {"wiki": str(wiki), "terms": words + phrases, "results": results}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="*")
    ap.add_argument("-k", type=int, default=8, help="results to return (default 8)")
    ap.add_argument("--per-page", type=int, default=2, help="max chunks per page (default 2)")
    ap.add_argument("--wiki", type=Path, default=None, help="wiki folder (default: <vault>/wiki)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--index-only", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()

    wiki = (a.wiki or default_wiki()).resolve()
    if not (wiki / "index.md").is_file():
        sys.exit(f"error: no wiki/index.md under {wiki}")
    db = open_db(wiki, a.rebuild)
    changed, removed = sync_index(db, wiki)
    n_chunks = db.execute("SELECT count(*) FROM chunks").fetchone()[0]
    n_pages = db.execute("SELECT count(*) FROM files").fetchone()[0]

    if a.index_only or not a.query:
        print(f"indexed {n_pages} pages / {n_chunks} chunks (re-indexed {changed}, removed {removed})")
        return

    out = search(db, wiki, " ".join(a.query), a.k, a.per_page)
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    print(f"wiki: {out['wiki']}")
    print(f"bm25 | {n_pages} pages / {n_chunks} chunks | terms: {', '.join(out['terms'])}")
    if not out["results"]:
        print("no matches")
    for i, r in enumerate(out["results"], 1):
        head = f"  § {r['heading']}" if r["heading"] else ""
        print(f"{i}. {r['path']}:{r['lines'][0]}-{r['lines'][1]}{head}  [{r['score']}]")
        if r["snippet"]:
            print(f"   {r['snippet']}")


if __name__ == "__main__":
    main()
