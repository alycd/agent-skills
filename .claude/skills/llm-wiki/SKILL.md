---
name: llm-wiki
description: >
  Multimodal Wiki Knowledge Graph Skill. Supports ingesting PDF, DOCX, PPTX, XLSX, Markdown, images and other formats
  into structured Wiki, and automatically builds interactive knowledge graphs (graph.html).
  Activates when user says "wiki-ingest", "wiki 摄入", "build knowledge graph", "wiki-graph", "wiki-query",
  "wiki-lint", "wiki 检查", "add document to wiki", "knowledge base construction",
  "wiki-config", "wiki configuration", "set wiki path",
  "wiki-input", "wiki 输入".
  DEFERRAL: if the current working directory is inside a project that has its own project-scoped wiki
  skill (e.g. a wiki-related skill under that project's .claude/skills/, such as "vault-wiki"), use that
  project skill instead of this one for all wiki-ingest/wiki-query/wiki-lint style requests — this
  skill's workspace (~/Documents/llm-wiki) is unrelated to that project's content.
triggers:
  - wiki-ingest
  - wiki 摄入
  - wiki-graph
  - 构建知识图谱
  - wiki-query
  - wiki 查询
  - wiki-lint
  - wiki 检查
  - 知识库构建
  - 把文档加入 wiki
  - wiki-config
  - wiki workspace
  - 设置 wiki 路径
  - wiki 配置
  - wiki-input
  - wiki 输入
---

# LLM Wiki — Multimodal Knowledge Graph Skill

## Design Philosophy

> *"LLM writes and maintains wiki; humans read and ask questions."*

This skill implements a Karpathy-style knowledge management system: raw documents are ingested into `raw/`, LLM compiles them into durable structured wiki pages, and continuously cross-references and updates them over time. The core difference from RAG is: **knowledge is synthesized at ingest time, not at query time**, making the knowledge base grow with compound interest with each ingestion.

---

## Directory Structure

```
<project-root>/
  raw/                  # Raw documents (never modify)
    <topic>/            # First-level subdirectories organized by topic, no nesting
  wiki/
    index.md            # Directory of all pages (organized by topic sections)
    overview.md         # Cross-source synthesis summary (living synthesis)
    log.md              # Append-only operation log
    sources/            # Summary page for each raw document
    entities/           # People / Companies / Projects / Products
    concepts/           # Concepts / Frameworks / Methodologies
    syntheses/          # Archived query answers
    archive/            # Archived outdated pages
  graph/
    graph.json          # Nodes + edges data
    graph.html          # Self-contained vis.js visualization
```

> `raw/` only allows one-level subdirectories (e.g., `raw/papers/`, `raw/slides/`), deeper nesting is not supported.

---

## Page Format (Frontmatter)

Each wiki page uses the following frontmatter:

```yaml
---
title: "Page Title"
type: source | entity | concept | synthesis
tags: []
sources: []            # List of source slugs (for entity/concept/synthesis)
date: YYYY-MM-DD       # Only for source type: original document date
source_file: raw/...   # Only for source type: archive path
source_type: pdf | docx | pptx | xlsx | markdown | image  # Only for source type
last_updated: YYYY-MM-DD
---
```

Pages reference each other using `[[PageName]]` wikilink format.

**Link Path Conventions**:
- Same-topic links: use filename directly `[[ArticleName]]`
- Cross-topic links: use relative path `[[../other-topic/ArticleName]]`

---

## Workspace Configuration

Before executing any wiki command, determine **WIKI_ROOT** in this order:

1. **Explicit command-line path** — Command contains `@<path>` parameter (e.g., `wiki-ingest raw/papers/x.pdf @/data/myproject`)
2. **Config file** — Read `.claude/config/llm-wiki.json`, use `workspace` field (expand `~` to absolute path)
3. **Current working directory** — If neither is configured, use `cwd`

**Once WIKI_ROOT is determined, it must not be changed for any reason, nor inferred or overridden from command arguments (e.g., file path from `wiki-input`).**

### When WIKI_ROOT Directory Doesn't Exist

If the determined WIKI_ROOT path doesn't exist on the filesystem, **directly create the complete directory structure at that path**, then continue executing the command:

```
<WIKI_ROOT>/
  raw/
    inbox/            # Default archive directory when wiki-input doesn't specify topic
  wiki/
    sources/
    entities/
    concepts/
    syntheses/
    archive/
  graph/
```

Also initialize three base files:

**`wiki/index.md`**:
```markdown
# Wiki Index

_Last updated: YYYY-MM-DD_
```

**`wiki/overview.md`**:
```markdown
# Wiki Overview

_No content yet, will be auto-generated after first ingestion._
```

**`wiki/log.md`**:
```markdown
# Wiki Log

Append-only chronological record of all operations.

Format: `## [YYYY-MM-DD] <operation> | <title>`

Parse recent entries: `grep "^## \[" wiki/log.md | tail -10`

---
```

**Config file format** (`.claude/config/llm-wiki.json`):

```json
{
  "workspace": "/Users/me/projects/my-wiki",
  "description": "Optional notes"
}
```

> Config file is saved in the Claude Code project root's `.claude/` directory, unrelated to the wiki workspace.
> Use `wiki-config workspace <path>` to create or update config, `wiki-config show` to view current config.

---

## Command Reference

| User Command | Triggered Workflow | Reference Doc |
|---|---|---|
| `wiki-config workspace <path>` / `设置 wiki 路径` | Config workflow | [references/wiki-config.md](references/wiki-config.md) |
| `wiki-config show` | Config workflow | [references/wiki-config.md](references/wiki-config.md) |
| `wiki-config reset` | Config workflow | [references/wiki-config.md](references/wiki-config.md) |
| `wiki-input <path>` / `wiki 输入 <path>` | Input workflow | [references/wiki-input.md](references/wiki-input.md) |
| `wiki-ingest <file>` / `把 <file> 加入 wiki` | Ingest workflow | [references/wiki-ingest.md](references/wiki-ingest.md) |
| `wiki-query: <question>` / `wiki 查询：<question>` | Query workflow | [references/wiki-query.md](references/wiki-query.md) |
| `wiki-lint` / `wiki 检查` | Lint workflow | [references/wiki-lint.md](references/wiki-lint.md) |
| `wiki-graph` / `构建知识图谱` | Graph workflow | [references/wiki-graph.md](references/wiki-graph.md) |

> See `references/` directory for detailed parameter formats, examples, and notes for each command.
> Page templates see [templates/wiki-page-templates.md](templates/wiki-page-templates.md).

**`wiki-input` vs `wiki-ingest` — Which to use?**

| | `wiki-input` | `wiki-ingest` |
|---|---|---|
| File source | Any local or remote path | Already in `raw/` directory |
| Archive behavior | Auto-copy to `raw/<topic>/` | Not needed, read directly |
| Use case | Daily use (recommended) | Workflow with manual raw/ management |

---

## Input Workflow (Arbitrary Path Ingestion)

**Trigger**: `wiki-input <path> [--topic <slug>]` or `wiki 输入 <path>`

Accepts files from any local or remote path, **copies to `raw/<topic>/` for archiving then ingests**. WIKI_ROOT is strictly resolved from config file, unrelated to input file path.

### Step 0 — Determine WIKI_ROOT

Parse in standard order (`@<path>` → `.claude/config/llm-wiki.json` → `cwd`), create directory if doesn't exist. **Do not infer WIKI_ROOT from input file path; do not fallback to cwd when config file exists.**

### Step 1 — Path Resolution and Validation

Expand path (`~` → home, Windows `C:/` used directly, relative paths based on cwd), verify file exists and format is supported.
Remote paths (`oss://`, `s3://`, `http(s)://`) are first downloaded to temp directory, temp files deleted after Ingest completes (archive copy in `raw/` is preserved).

### Step 1.5 — Determine Topic and Archive to raw/

Copy original file to `raw/<topic>/` as permanent archive, `source_file` field records this archive path.

**Topic Determination Logic:**

1. **Explicit specification**: Command-line `--topic <slug>` passed, use directly
2. **Fallback**: If not specified, put in `raw/inbox/`, and prompt user they can manually move and re-ingest later

**Topic slug rules**: All lowercase, only `a-z`, `0-9`, hyphens, max 32 characters.

If `raw/<topic>/` doesn't exist, create it. If same-name file exists, ask user whether to overwrite.

### Step 2 — Trigger Ingest Workflow

Execute complete Ingest flow (dedup → extract → Wiki write). `source_file` field records `raw/<topic>/<filename>` path.

> Full parameter specs and OSS support analysis see [references/wiki-input.md](references/wiki-input.md).

---

## Ingest Workflow (Multimodal Ingestion)

**Trigger**: `wiki-ingest <file>` or `把 <file> 加入 wiki`

### Step 0 — Determine WIKI_ROOT

Parse workspace path in priority order (command-line `@<path>` → `.claude/config/llm-wiki.json` → cwd), expand `~` to absolute path. If directory doesn't exist, auto-create complete directory structure then continue. All subsequent paths are relative to WIKI_ROOT.

### Step 1 — Deduplication Check

Read `wiki/log.md`, check if this file already has an ingest record (match by filename). If exists, ask user whether to force re-ingest.

### Step 2 — Multimodal Content Extraction

Call corresponding skill based on file type to convert content to plain text:

| File Type | Extraction Method |
|---|---|
| `.md` `.txt` `.json` `.yaml` | Direct `Read` tool |
| `.pdf` | Call `pdf` skill — `pdfplumber` extracts text+tables |
| `.docx` | Call `docx` skill — `python-docx` extracts body+tables+headings |
| `.pptx` | Call `pptx` skill — Extract each slide's title+body+notes |
| `.xlsx` `.csv` | Call `xlsx` skill — Extract worksheet content, convert to Markdown tables |
| `.png` `.jpg` `.jpeg` `.webp` | Use Claude vision to read image content directly |

Extraction result is unified to **Markdown format plain text**, preserving heading hierarchy and table structure.

### Step 2-10 — Standard Wiki Write

After content extraction, execute these steps (strictly in order):

1. **Read** `wiki/index.md` and `wiki/overview.md` to get current wiki context
2. **Read** recent 5 source pages to establish cross-reference context
3. **Write** `wiki/sources/<slug>.md` — Create source summary page per Source Page Format
4. **Update** `wiki/index.md` — Append new entry in corresponding topic section
5. **Update** `wiki/overview.md` — Revise cross-source synthesis summary
6. **Create/Update** `wiki/entities/` — Create or update pages for key people, companies, projects
7. **Create/Update** `wiki/concepts/` — Create or update pages for key concepts, frameworks
8. **Mark contradictions** — Annotate conflicts with existing wiki content in related pages' `## Contradictions` section
9. **Append log** `wiki/log.md`: `## [YYYY-MM-DD] ingest | <Title>`
10. **Output summary** — Which pages were created, which updated, which contradictions found

### Source Page Format

```markdown
---
title: "Source Title"
type: source
tags: []
date: YYYY-MM-DD
source_file: raw/...
source_type: pdf | docx | pptx | xlsx | markdown | image
last_updated: YYYY-MM-DD
---

## Summary
2-4 sentence summary.

## Key Claims
- Point 1
- Point 2

## Key Quotes / Key Data
> "Quote content" — Context (quote no more than 125 characters)

## Connections
- [[EntityName]] — Connection reason
- [[ConceptName]] — Connection type

## Contradictions
- Conflicts with [[OtherPage]] on: ...
```

---

## Query Workflow

**Trigger**: `wiki-query: <question>` or `wiki 查询：<question>`

0. Parse WIKI_ROOT (command-line `@<path>` → `.claude/config/llm-wiki.json` → cwd)
1. If wiki is empty (no `wiki/index.md` or index has no entries), prompt user to run `wiki-ingest` first
2. Read `wiki/index.md`, identify pages most relevant to question (max 10 pages)
3. Use `Read` tool to read each page
4. Synthesize answer, use `[[PageName]]` wikilink for inline citations; direct quotes no more than 125 characters
5. Append `## Sources` section at end of answer, list all referenced page paths
6. Ask user if they want to save answer as `wiki/syntheses/<slug>.md`
7. Append log: `## [YYYY-MM-DD] query | <question summary>`

---

## Lint Workflow

**Trigger**: `wiki-lint` or `wiki 检查`

**Step 0** — Parse WIKI_ROOT (`.claude/config/llm-wiki.json` → cwd), all paths based on WIKI_ROOT. If `wiki/index.md` doesn't exist or has no entries, prompt user to run `wiki-ingest` first, then stop.

### Phase One — Deterministic Checks (Grep + Read)

- **Orphaned pages** — Pages not referenced by any other page's `[[link]]`
- **Broken links** — `[[WikiLink]]` pointing to non-existent pages
- **Index consistency** — Whether pages listed in `wiki/index.md` actually exist
- **Missing entity pages** — Entities mentioned in 3+ pages but without standalone pages

### Phase Two — Semantic Analysis (Claude reads max 20 page samples)

- **Content contradictions** — Conflicting claims across pages
- **Outdated summaries** — Pages not updated after newer source ingestion
- **Underdeveloped concepts** — Thin concept pages referenced in many places
- **Knowledge gaps** — Typical questions the wiki can't answer, suggest supplementing sources

### Output

Generate structured lint report, organized by category and severity. Ask whether to save as `wiki/lint-report.md`.
Append log: `## [YYYY-MM-DD] lint | Wiki health check`

---

## Graph Workflow

**Trigger**: `wiki-graph` or `构建知识图谱`

**Step 0** — Parse WIKI_ROOT (`.claude/config/llm-wiki.json` → cwd), script path and wiki path both based on WIKI_ROOT.

### Method A — Execute Python Script (Preferred)

```bash
cd <WIKI_ROOT>
python <skill-root>/scripts/build_graph.py [--skip-infer] [--open]
```

> **Note**: Script uses relative paths, must execute in WIKI_ROOT directory (the directory containing `wiki/` and `graph/` subdirectories).

Parameter description:
- `--skip-infer`: Skip AI semantic inference, only extract explicit wikilinks (fast mode, no `ANTHROPIC_API_KEY` needed)
- `--open`: Auto-open `graph/graph.html` in browser after build completes

Script supports incremental caching, pages with unchanged content reuse previous inference results, cache stored in `graph/.graph_cache.json`.

Dependencies: `pip install networkx python-louvain anthropic`

### Method B — Pure Claude Manual Build (When no Python environment)

1. Use `Grep` to find all `[[wikilinks]]` under `wiki/`
2. Build node list: Each wiki page is a node, type from frontmatter
3. Build edge list: Explicit wikilink marked as `EXTRACTED`, semantic inferred edges (confidence ≥ 0.5) marked as `INFERRED` (with confidence 0-1), inferred edges with confidence < 0.5 filtered out
4. Write `graph/graph.json` (format below)
5. Write `graph/graph.html` (using vis.js template, see end of this file)
6. Append log: `## [YYYY-MM-DD] graph | Knowledge graph rebuilt`
7. Output stats: node count, edge count, type distribution, top 5 hub pages

### graph.json Format

```json
{
  "build_date": "YYYY-MM-DD",
  "nodes": [
    {
      "id": "wiki/concepts/RAG.md",
      "label": "RAG",
      "type": "concept",
      "community": 0,
      "degree": 5
    }
  ],
  "edges": [
    {
      "source": "wiki/sources/paper-rag.md",
      "target": "wiki/concepts/RAG.md",
      "type": "EXTRACTED"
    },
    {
      "source": "wiki/concepts/RAG.md",
      "target": "wiki/concepts/VectorDB.md",
      "type": "INFERRED",
      "confidence": 0.85,
      "label": "depends on"
    }
  ]
}
```

Field descriptions:
- `nodes[].community`: Louvain community number (integer), auto-calculated when `python-louvain` installed; otherwise all `0`
- `nodes[].degree`: Sum of in/out degrees for the node (edge connection count)
- `edges[].type`: `EXTRACTED` (explicit wikilink) or `INFERRED` (AI inferred, confidence ≥ 0.5)

### Node Color Specification

| type | Color |
|---|---|
| source | `#4A90D9` (blue) |
| entity | `#E8A838` (orange) |
| concept | `#5BA85A` (green) |
| synthesis | `#9B59B6` (purple) |

---

## Naming Conventions

- Source slug: `kebab-case`, consistent with original filename
- Entity pages: `TitleCase.md` (e.g., `OpenAI.md`, `SamAltman.md`)
- Concept pages: `TitleCase.md` (e.g., `ReinforcementLearning.md`, `RAG.md`)
- Source pages: `kebab-case.md`
- Archive pages: Keep original filename, move to `wiki/archive/`

---

## Archive Mechanism

When a wiki page's content is completely superseded by an updated page, or the source document is outdated, it can be archived:

1. Move file to `wiki/archive/`
2. In referencing pages, update `[[PageName]]` to `[[archive/PageName]]` (add `[Archived]` tag)
3. Append log: `## [YYYY-MM-DD] archive | <PageName>`

> Archive is a snapshot, doesn't update with source page changes.

---

## vis.js HTML Template

When manually generating `graph/graph.html`, use [`templates/wiki-graph-template.html`](templates/wiki-graph-template.html) as the template framework.

Replace `/* GRAPH_JSON_PLACEHOLDER */` in the file with actual JSON content from `graph.json` to get a zero-dependency self-contained HTML file.

---

## Multimodal Extraction Detailed Specs

### PDF Extraction

```python
import pdfplumber

def extract_pdf(path: str) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            parts.append(f"<!-- Page {i+1} -->\n{text}")
            for tbl in tables:
                if tbl:
                    header = " | ".join(str(c) for c in tbl[0])
                    sep = " | ".join(["---"] * len(tbl[0]))
                    rows = "\n".join(" | ".join(str(c) for c in r) for r in tbl[1:])
                    parts.append(f"\n| {header} |\n| {sep} |\n{rows}\n")
    return "\n\n".join(parts)
```

### DOCX Extraction

```python
from docx import Document

def extract_docx(path: str) -> str:
    doc = Document(path)
    parts = []
    for para in doc.paragraphs:
        if para.style.name.startswith("Heading"):
            level = para.style.name.split(" ")[-1]
            parts.append(f"{'#' * int(level)} {para.text}")
        elif para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        rows = [[c.text for c in r.cells] for r in table.rows]
        if rows:
            header = " | ".join(rows[0])
            sep = " | ".join(["---"] * len(rows[0]))
            body = "\n".join(" | ".join(r) for r in rows[1:])
            parts.append(f"| {header} |\n| {sep} |\n{body}")
    return "\n\n".join(parts)
```

### PPTX Extraction

```python
from pptx import Presentation

def extract_pptx(path: str) -> str:
    prs = Presentation(path)
    parts = []
    for i, slide in enumerate(prs.slides):
        slide_parts = [f"## Slide {i+1}"]
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        slide_parts.append(text)
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_parts.append(f"_Notes: {notes}_")
        parts.append("\n".join(slide_parts))
    return "\n\n---\n\n".join(parts)
```

### XLSX Extraction

```python
import pandas as pd

def extract_xlsx(path: str) -> str:
    xl = pd.ExcelFile(path)
    parts = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet).fillna("")
        md = df.to_markdown(index=False)
        parts.append(f"### Sheet: {sheet}\n\n{md}")
    return "\n\n".join(parts)
```

---

## Image Content Understanding

For `.png`, `.jpg`, `.jpeg`, `.webp` and other image files, use Claude's vision capability directly (`Read` tool to read image file), extract text and structure from charts, flowcharts, table screenshots, convert to Markdown description before entering Ingest workflow.

---

## Important Notes

1. **Never modify** raw documents in `raw/` directory
2. Before each ingest, check `wiki/log.md` to confirm if already ingested, avoid duplicates
3. Contradiction annotation priority is higher than content update, annotate first then overwrite
4. graph.html should be self-contained (inline JSON data), no server needed
5. For batch ingestion, process files one by one, append one log entry after each file completes
6. `wiki/index.md` is organized by topic sections, each topic maintains article list (with summary and update date)
7. `wiki/log.md` is append-only, never modify historical records, it's the complete audit trail of wiki evolution

---

## Interruption and Recovery

Multi-step workflows (especially the 10-step `wiki-ingest` flow) may be interrupted due to network, session timeout, or user interruption.

### Determining Interruption

`wiki/log.md` is the only completion status indicator:

- **Log has `ingest` entry for this file** → Normal completion, no action needed
- **`wiki/sources/<slug>.md` exists, but log has no corresponding entry** → Previous ingest interrupted before step 9
- **No corresponding file in `wiki/sources/`** → Ingest interrupted at early steps or never started

### Recovery Method

Re-run `wiki-ingest <file>`, during dedup check (Step 0) the system will prompt "No log record found, continue?" — choose to continue and re-execute the complete flow from start. If some pages were already written, re-ingest will overwrite with latest version, won't produce duplicate content.

### Batch Ingestion Interruption

During batch ingestion (multiple files), log is appended immediately after each file completes. After interruption, just continue from **the file after the last log entry**, already completed files don't need to be re-processed.
