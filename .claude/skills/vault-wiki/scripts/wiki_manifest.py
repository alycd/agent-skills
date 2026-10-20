#!/usr/bin/env python3
"""Ingest dedup manifest: wiki/.manifest.json maps original filename -> content hash + slug.

Usage:
  wiki_manifest.py check <path>         # prints: new | same | changed | duplicate-of <file>
  wiki_manifest.py add <path> <slug>    # record a completed ingest
  wiki_manifest.py rebuild              # backfill from sources/*.md `source_file` frontmatter

`check` compares content, not just names: a renamed copy of an ingested file is reported as
`duplicate-of`, and an edited file with the same name as `changed` (re-ingest it).
Exit code 0 for new/changed, 1 for same/duplicate, 2 for errors.
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path


def default_wiki():
    return Path(__file__).resolve().parents[4] / "wiki"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(wiki):
    p = wiki / ".manifest.json"
    return json.loads(p.read_text()) if p.is_file() else {}


def save(wiki, data):
    (wiki / ".manifest.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def check(wiki, path):
    data, digest, name = load(wiki), sha(path), path.name
    if name in data:
        return "same" if data[name]["sha256"] == digest else "changed"
    for other, rec in data.items():
        if rec["sha256"] == digest:
            return f"duplicate-of {other}"
    return "new"


def rebuild(wiki):
    vault, data, missing = wiki.parent, load(wiki), []
    for page in sorted((wiki / "sources").glob("*.md")):
        m = re.search(r"^source_file:\s*\"?([^\"\n]+)\"?", page.read_text(encoding="utf-8"), re.M)
        if not m:
            continue
        sf = m.group(1).strip()
        src = next((c for c in (wiki / sf, vault / sf) if c.is_file()), None)
        if src is None:
            missing.append(f"{page.stem}: {sf}")
            continue
        data.setdefault(src.name, {"sha256": sha(src), "slug": page.stem,
                                   "source_file": sf, "ingested": "backfill"})
    save(wiki, data)
    return len(data), missing


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "add", "rebuild"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--wiki", type=Path, default=None)
    a = ap.parse_args()
    wiki = (a.wiki or default_wiki()).resolve()

    if a.cmd == "rebuild":
        n, missing = rebuild(wiki)
        print(f"manifest: {n} entries")
        for m in missing:
            print(f"source file not found: {m}")
        return
    if not a.args:
        sys.exit("error: path required")
    path = Path(a.args[0]).expanduser().resolve()
    if not path.is_file():
        print(f"error: not a file: {path}")
        sys.exit(2)
    if a.cmd == "check":
        result = check(wiki, path)
        print(result)
        sys.exit(0 if result in ("new", "changed") else 1)
    if len(a.args) < 2:
        sys.exit("error: add needs <path> <slug>")
    data = load(wiki)
    try:
        sf = path.relative_to(wiki).as_posix()
    except ValueError:
        sf = path.relative_to(wiki.parent).as_posix() if wiki.parent in path.parents else str(path)
    data[path.name] = {"sha256": sha(path), "slug": a.args[1], "source_file": sf,
                       "ingested": datetime.date.today().isoformat()}
    save(wiki, data)
    print(f"recorded {path.name} -> {a.args[1]}")


if __name__ == "__main__":
    main()
