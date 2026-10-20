#!/usr/bin/env python3
"""
build_graph.py — LLM Wiki Knowledge Graph Builder

Two-pass scan:
  Pass 1: Parse all [[wikilinks]] in wiki pages → EXTRACTED edges
  Pass 2: Call Claude to infer implicit semantic relations → INFERRED edges (with confidence)

Supports SHA256 caching, only processes changed pages.
Output: graph/graph.json + graph/graph.html (vis.js self-contained)

Usage:
  python build_graph.py              # Full build
  python build_graph.py --skip-infer # Skip AI inference (fast mode)
  python build_graph.py --open       # Open browser after build
"""

import argparse
import hashlib
import json
import os
import re
import sys
import webbrowser
from datetime import date
from pathlib import Path

# ── Optional Dependencies ───────────────────────────────────────────────────────
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import community as community_louvain
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

# ── Constants ──────────────────────────────────────────────────────────────────
WIKI_DIR = Path("wiki")
GRAPH_DIR = Path("graph")
CACHE_FILE = GRAPH_DIR / ".graph_cache.json"
GRAPH_JSON = GRAPH_DIR / "graph.json"
GRAPH_HTML = GRAPH_DIR / "graph.html"
LOG_FILE   = WIKI_DIR / "log.md"
TEMPLATE_FILE = Path(__file__).parent.parent / "templates" / "wiki-graph-template.html"

NODE_COLORS = {
    "source":    "#4A90D9",
    "entity":    "#E8A838",
    "concept":   "#5BA85A",
    "synthesis": "#9B59B6",
}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:\|[^\]]+?)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---", re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)
TYPE_RE  = re.compile(r'^type:\s*(\S+)',  re.MULTILINE)


# ── Utility Functions ──────────────────────────────────────────────────────────

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def slug_to_id(path: Path) -> str:
    return path.as_posix()


def parse_frontmatter(content: str) -> dict:
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    fm = m.group(1)
    title = TITLE_RE.search(fm)
    typ   = TYPE_RE.search(fm)
    return {
        "title": title.group(1).strip() if title else None,
        "type":  typ.group(1).strip()   if typ   else "source",
    }


def collect_pages() -> list[Path]:
    """Return all .md page paths under wiki/ (excluding index/log/overview/lint-report)"""
    skip = {"index.md", "log.md", "overview.md", "lint-report.md"}
    pages = []
    for p in WIKI_DIR.rglob("*.md"):
        if p.name not in skip:
            pages.append(p)
    return pages


def extract_wikilinks(content: str) -> list[str]:
    return WIKILINK_RE.findall(content)


def resolve_link(link_text: str, all_page_labels: dict[str, str]) -> str | None:
    """Match [[LinkText]] to actual file ID, prefer exact label match, then try TitleCase path guess"""
    for pid, label in all_page_labels.items():
        if label.lower() == link_text.lower():
            return pid
    # Guess path
    for subdir in ("entities", "concepts", "sources", "syntheses"):
        guess = WIKI_DIR / subdir / f"{link_text}.md"
        if guess.exists():
            return slug_to_id(guess)
    return None


# ── Pass 1: Extract Explicit Links ──────────────────────────────────────────────

def build_extracted_edges(pages: list[Path]) -> tuple[dict, list[dict]]:
    """
    Returns:
        nodes_map: {id: {id, label, type, content_hash}}
        edges: [{source, target, type="EXTRACTED"}]
    """
    nodes_map: dict[str, dict] = {}
    raw_edges: list[tuple[str, str]] = []  # (source_id, link_text)

    for p in pages:
        content = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        pid = slug_to_id(p)
        nodes_map[pid] = {
            "id":           pid,
            "label":        fm.get("title") or p.stem,
            "type":         fm.get("type",  "source"),
            "content_hash": sha256(content),
        }
        for link in extract_wikilinks(content):
            raw_edges.append((pid, link))

    label_map = {pid: n["label"] for pid, n in nodes_map.items()}
    edges: list[dict] = []
    for src, link_text in raw_edges:
        tgt = resolve_link(link_text, label_map)
        if tgt and tgt in nodes_map and tgt != src:
            edges.append({"source": src, "target": tgt, "type": "EXTRACTED"})

    return nodes_map, edges


# ── Pass 2: AI Inference of Implicit Relations ────────────────────────────────

INFER_PROMPT = """You are analyzing a wiki knowledge base. Given a list of wiki pages and their types,
identify implicit semantic relationships that are NOT already captured by explicit wikilinks.

For each relationship found, output JSON array entries:
{{"source": "<page_id>", "target": "<page_id>", "label": "<short relationship>", "confidence": 0.0-1.0}}

Only include confidence >= 0.5. Mark as INFERRED type (caller will add this).
Output ONLY a valid JSON array, nothing else.

Pages:
{pages_json}
"""


def infer_edges(nodes_map: dict, skip_infer: bool, cache: dict) -> list[dict]:
    if skip_infer or not HAS_ANTHROPIC:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠  ANTHROPIC_API_KEY not set — skipping inference pass", file=sys.stderr)
        return []

    # Only process pages with changed content
    changed_ids = [
        pid for pid, n in nodes_map.items()
        if cache.get(pid) != n["content_hash"]
    ]
    if not changed_ids:
        print("✓ No changed pages — reusing cached inferred edges")
        return cache.get("inferred_edges", [])

    pages_json = json.dumps(
        [{"id": pid, "label": nodes_map[pid]["label"], "type": nodes_map[pid]["type"]}
         for pid in list(nodes_map)[:80]],   # Limit tokens
        ensure_ascii=False,
        indent=2
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": INFER_PROMPT.format(pages_json=pages_json)}],
    )
    raw = msg.content[0].text.strip()
    # Remove possible ```json wrapper
    raw = re.sub(r"^```json\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        inferred = json.loads(raw)
    except json.JSONDecodeError:
        print("⚠  Could not parse inferred edges JSON", file=sys.stderr)
        return []

    edges = [
        {
            "source":     e["source"],
            "target":     e["target"],
            "type":       "INFERRED",
            "label":      e.get("label", ""),
            "confidence": e.get("confidence", 0.7),
        }
        for e in inferred
        if e.get("source") in nodes_map and e.get("target") in nodes_map
        and e.get("confidence", 0) >= 0.5
    ]
    return edges


# ── Community Detection ────────────────────────────────────────────────────────

def detect_communities(nodes_map: dict, edges: list[dict]) -> dict[str, int]:
    if not HAS_NX:
        return {pid: 0 for pid in nodes_map}

    G = nx.Graph()
    for pid in nodes_map:
        G.add_node(pid)
    for e in edges:
        G.add_edge(e["source"], e["target"])

    partition = community_louvain.best_partition(G)
    return partition


# ── Generate graph.html ───────────────────────────────────────────────────────

# ── Main Entry ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build wiki knowledge graph")
    parser.add_argument("--skip-infer", action="store_true",
                        help="Skip AI inference pass (faster)")
    parser.add_argument("--open", action="store_true",
                        help="Open graph.html in browser after build")
    args = parser.parse_args()

    GRAPH_DIR.mkdir(exist_ok=True)

    # Load cache
    cache: dict = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
        except Exception:
            pass

    # Collect pages
    pages = collect_pages()
    if not pages:
        print("No wiki pages found in wiki/. Run `wiki ingest` first.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(pages)} wiki pages")

    # Pass 1
    nodes_map, extracted_edges = build_extracted_edges(pages)
    print(f"Pass 1: {len(extracted_edges)} extracted edges")

    # Pass 2
    inferred_edges = infer_edges(nodes_map, args.skip_infer, cache)
    print(f"Pass 2: {len(inferred_edges)} inferred edges")

    all_edges = extracted_edges + inferred_edges

    # Community detection
    partition = detect_communities(nodes_map, all_edges)

    # Calculate degree
    degree: dict[str, int] = {pid: 0 for pid in nodes_map}
    for e in all_edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1

    nodes_out = [
        {
            "id":        n["id"],
            "label":     n["label"],
            "type":      n["type"],
            "community": partition.get(n["id"], 0),
            "degree":    degree.get(n["id"], 0),
        }
        for n in nodes_map.values()
    ]

    graph_data = {
        "build_date": str(date.today()),
        "nodes":      nodes_out,
        "edges":      all_edges,
    }

    # Write graph.json
    GRAPH_JSON.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2))
    print(f"Written {GRAPH_JSON}")

    # Write graph.html
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    html = template.replace("/* GRAPH_JSON_PLACEHOLDER */", json.dumps(graph_data, ensure_ascii=False))
    GRAPH_HTML.write_text(html, encoding="utf-8")
    print(f"Written {GRAPH_HTML}")

    # Update cache
    new_cache = {pid: n["content_hash"] for pid, n in nodes_map.items()}
    new_cache["inferred_edges"] = inferred_edges
    CACHE_FILE.write_text(json.dumps(new_cache, indent=2))

    # Append log
    log_entry = f"\n## [{date.today()}] graph | Knowledge graph rebuilt — {len(nodes_out)} nodes, {len(all_edges)} edges\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # Stats for hub pages
    top_hubs = sorted(nodes_out, key=lambda n: n["degree"], reverse=True)[:5]
    print("\n=== Graph Stats ===")
    print(f"Nodes: {len(nodes_out)}")
    print(f"Edges: {len(all_edges)} (extracted={len(extracted_edges)}, inferred={len(inferred_edges)})")
    print("Top hub pages:")
    for n in top_hubs:
        print(f"  {n['label']} ({n['type']}) — degree {n['degree']}")

    if args.open:
        webbrowser.open(GRAPH_HTML.resolve().as_uri())


if __name__ == "__main__":
    main()
