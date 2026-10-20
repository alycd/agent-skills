#!/usr/bin/env python3
"""Deterministic health check for the vault wiki (no LLM).

Usage: wiki_lint.py [--wiki PATH] [--json] [--min-sources 3]

Checks, most severe first:
  1. broken links      — [[targets]] that resolve to no file
  2. index consistency — index.md entries whose page doesn't exist
  3. orphans           — managed pages with no inbound link and not in index.md
  4. missing entities  — capitalised names in N+ source pages with no entity/concept page
                         (heuristic candidates: review before creating pages)
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

MANAGED_DIRS = ["sources", "entities", "concepts", "syntheses"]
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
NAME_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:[- ][A-Z][A-Za-z0-9]*)*\b")
SECTION_WORDS = {"Summary", "Key Claims", "Key Quotes", "Key Data", "Connections", "Contradictions",
                 "None", "See Also", "Overview", "Role", "Notes", "Sources", "Not", "No", "The", "This",
                 "These", "That", "It", "A", "An", "In", "On", "For", "With", "And", "Or", "But", "If",
                 "Per", "See", "Use", "Section", "Conflicts", "Document-Derived Facts", "TBD",
                 "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec",
                 "January", "February", "March", "April", "June", "July", "August", "September",
                 "October", "November", "December", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}


def default_wiki():
    return Path(__file__).resolve().parents[4] / "wiki"


def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`]*`", "", text)


def body_of(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def build_resolver(wiki):
    vault = wiki.parent
    by_stem = defaultdict(list)
    for p in wiki.rglob("*"):
        if p.is_file() and ".search" not in p.parts:
            by_stem[p.stem.lower()].append(p)
            by_stem[p.name.lower()].append(p)

    def resolve(target, from_page):
        t = target.strip()
        for base in (from_page.parent, wiki, vault):
            for cand in (base / t, base / (t + ".md")):
                try:
                    if cand.resolve().is_file():
                        return cand.resolve()
                except OSError:
                    pass
        # Obsidian-style: bare name matches a file anywhere in the wiki
        hits = by_stem.get(Path(t).name.lower(), [])
        return hits[0].resolve() if hits else None

    return resolve


def managed_pages(wiki):
    for d in MANAGED_DIRS:
        if (wiki / d).is_dir():
            yield from sorted((wiki / d).rglob("*.md"))


def lint(wiki, min_sources):
    resolve = build_resolver(wiki)
    pages = list(managed_pages(wiki))
    linkers = pages + [p for p in (wiki / "index.md", wiki / "overview.md") if p.is_file()]
    rel = lambda p: p.relative_to(wiki).as_posix()

    broken, index_bad, inbound = [], [], defaultdict(set)
    for page in linkers:
        text = strip_code(page.read_text(encoding="utf-8", errors="replace"))
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in LINK_RE.finditer(line):
                target = resolve(m.group(1), page)
                if target is None:
                    item = {"page": rel(page), "line": lineno, "link": m.group(1)}
                    (index_bad if page.name == "index.md" and page.parent == wiki else broken).append(item)
                elif target != page.resolve():
                    inbound[target].add(page.name if page.parent == wiki else rel(page))

    orphans = [rel(p) for p in pages if not inbound.get(p.resolve())]

    # missing entities: names in >= min_sources source pages, never written lowercase,
    # and not already a page title, filename or alias
    known = set()
    for p in pages:
        known.add(p.stem.lower())
        m = re.search(r'^title:\s*"?([^"\n]+)"?', p.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            known.add(m.group(1).strip().lower())
    idx = wiki / "index.md"
    if idx.is_file():
        for row in re.findall(r"^\|([^|\n]+)\|([^|\n]+)\|", idx.read_text(encoding="utf-8"), re.M):
            for n in [row[0]] + row[1].split(","):
                known.add(n.strip().lower())
    known_compact = {re.sub(r"[\s_-]", "", k) for k in known}

    seen_in = defaultdict(set)
    lowercase_words = set()
    for p in sorted((wiki / "sources").glob("*.md")) if (wiki / "sources").is_dir() else []:
        text = strip_code(body_of(p.read_text(encoding="utf-8", errors="replace")))
        text = LINK_RE.sub(" ", text)
        lowercase_words |= set(re.findall(r"\b[a-z][a-z0-9]+\b", text))
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                continue
            # drop the first word of each sentence (capitalised by grammar, not because it's a name)
            for sent in re.split(r"(?<=[.!?:])\s+|^\s*[-*>]\s*", line):
                for m in NAME_RE.finditer(sent):
                    if m.start() == len(sent) - len(sent.lstrip()) and " " not in m.group(0):
                        continue
                    seen_in[m.group(0)].add(p.stem)
    missing = []
    for name, srcs in seen_in.items():
        if len(srcs) < min_sources or name in SECTION_WORDS or len(name) < 3:
            continue
        if name.lower() in lowercase_words or re.sub(r"[\s_-]", "", name.lower()) in known_compact:
            continue
        missing.append({"name": name, "sources": len(srcs), "in": sorted(srcs)[:5]})
    missing.sort(key=lambda x: (-x["sources"], x["name"]))

    return {"pages": len(pages), "broken_links": broken, "index_inconsistent": index_bad,
            "orphans": orphans, "missing_entity_candidates": missing}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wiki", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-sources", type=int, default=3)
    a = ap.parse_args()
    wiki = (a.wiki or default_wiki()).resolve()
    if not (wiki / "index.md").is_file():
        sys.exit(f"error: no wiki/index.md under {wiki}")
    r = lint(wiki, a.min_sources)
    if a.json:
        print(json.dumps(r, indent=2))
        return
    print(f"# Wiki lint — {r['pages']} managed pages\n")
    print(f"## Broken links ({len(r['broken_links'])})")
    for b in r["broken_links"]:
        print(f"- {b['page']}:{b['line']} → [[{b['link']}]]")
    print(f"\n## Index inconsistencies ({len(r['index_inconsistent'])})")
    for b in r["index_inconsistent"]:
        print(f"- index.md:{b['line']} → [[{b['link']}]] (page missing)")
    print(f"\n## Orphaned pages ({len(r['orphans'])})")
    for o in r["orphans"]:
        print(f"- {o}")
    print(f"\n## Missing entity candidates ({len(r['missing_entity_candidates'])}) — heuristic, review")
    for m in r["missing_entity_candidates"]:
        print(f"- {m['name']} — {m['sources']} sources ({', '.join(m['in'])})")


if __name__ == "__main__":
    main()
