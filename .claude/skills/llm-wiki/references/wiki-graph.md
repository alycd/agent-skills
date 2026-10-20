# wiki-graph — Knowledge Graph Build Command

Build Wiki knowledge graph.

**Trigger**: `wiki-graph` or `构建知识图谱`

## Parameter

No parameters.

## Execution Flow

Execute according to **Graph Workflow** in SKILL.md:

### Method A — Python Script (Preferred)

> **Important**: Script uses relative paths, must execute in **WIKI_ROOT directory**.

```bash
cd <WIKI_ROOT>
python <skill-root>/scripts/build_graph.py [--skip-infer] [--open]
```

Parameter description:
- `--skip-infer`: Skip AI semantic inference, only extract explicit wikilinks (fast mode, no `ANTHROPIC_API_KEY` needed)
- `--open`: Auto-open `graph/graph.html` in browser after build completes

Script supports incremental caching, pages with unchanged content reuse previous inference results, cache stored in `graph/.graph_cache.json`.

Dependencies: `pip install networkx python-louvain anthropic`

### Method B — Claude Manual Build (When no Python environment)

1. Use Grep to find all `[[wikilinks]]` under `wiki/` directory
2. Build node list: Each wiki page is a node, type from frontmatter
3. Build edge list: Explicit wikilink marked as `EXTRACTED`, semantic inferred edges (confidence ≥ 0.5) marked as `INFERRED`, edges with confidence < 0.5 filtered out
4. Write `graph/graph.json` (contains build_date, nodes, edges)
5. Write `graph/graph.html` (use [../templates/wiki-graph-template.html](../templates/wiki-graph-template.html) inject data)
6. Append log to `wiki/log.md`: `## [today's date] graph | Knowledge graph rebuilt`
7. Output stats: node count, edge count, type distribution, top 5 hub pages
