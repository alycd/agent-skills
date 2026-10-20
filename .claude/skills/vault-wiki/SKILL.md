---
name: vault-wiki
description: >
  Lightweight wiki skill scoped to this vault's wiki/ folder. Ingests documents (PDF, DOCX, PPTX,
  XLSX, Markdown, images) into structured source/entity/concept pages, keeps wiki/index.md current,
  and answers questions against the wiki using local BM25 search (SQLite FTS5, scripts/). No graph building (use the graphify skill for that) and no
  multi-workspace config — WIKI_ROOT is always wiki/ in this vault.
  Activates when the user says "ingest <file>", "wiki-ingest", "wiki ingest", "add this to the wiki",
  "wiki-query:", "wiki query:", "wiki-lint", "wiki lint", or "check the wiki".
---

# Vault Wiki

A trimmed fork of llm-wiki: LLM writes and maintains the wiki, humans read and ask questions. `WIKI_ROOT` is always `wiki/` at the vault root — never prompt for or infer another path. No graph builder (use `graphify`). Lint is deterministic-only. Search, lint and dedup run as scripts (see **Scripts**) so they stay fast and token-cheap as the wiki grows.

## Directory Structure

```
wiki/
  index.md                  # Directory of all pages by topic, plus an ## Aliases table
  overview.md               # Cross-source synthesis (updated lazily on ingest)
  log.md                    # Append-only operation log
  original_sources/         # Archive of files ingested from OUTSIDE the vault (never modify)
  sources/                  # One summary page per ingested document
  entities/                 # People / companies / projects mentioned in sources
  concepts/                 # Frameworks / methodologies / technical concepts
  syntheses/                # Saved wiki-query answers
  archive/                  # Superseded pages
  .search/index.sqlite      # Search index (generated, safe to delete; rebuilds itself)
  .manifest.json            # Ingest dedup: filename -> content hash + slug
```

Pre-existing loose notes in `wiki/` are left exactly as-is — this skill only manages `index.md`, `overview.md`, `log.md` and the subfolders above. If `wiki/index.md` doesn't exist, create the skeleton (the three files and five subfolders) first.

## Page Format

```yaml
---
title: "Page Title"
type: source | entity | concept | synthesis
tags: []
sources: []            # entity/concept/synthesis: list of source slugs
date: YYYY-MM-DD       # source only: original document date
source_file: ...       # source only: vault-relative path
source_type: pdf | docx | pptx | xlsx | markdown | image  # source only
last_updated: YYYY-MM-DD
---
```

Pages link with `[[PageName]]`. Same folder: `[[ArticleName]]`. Cross-folder: `[[../sources/article-name]]`. Templates: [templates/wiki-page-templates.md](templates/wiki-page-templates.md).

## Commands

| Command | Workflow |
|---|---|
| `wiki query: <question>` / "ask the wiki" | **Query** — below |
| `ingest <path> [--topic <slug>]` / "add this to the wiki" | [references/ingest.md](references/ingest.md) — Read it first |
| `wiki lint` / "check the wiki" | [references/lint.md](references/lint.md) — Read it first |

## Scripts

Run from the vault root with `python3`. Stdlib only; each syncs/locates `wiki/` itself.

| Script | Use |
|---|---|
| `.claude/skills/vault-wiki/scripts/wiki_search.py "<terms>" [-k 8]` | Ranked search: prints `path:start-end § heading` + snippet per hit. Paths are relative to `wiki/`. |
| `.claude/skills/vault-wiki/scripts/wiki_lint.py` | Deterministic lint report |
| `.claude/skills/vault-wiki/scripts/wiki_manifest.py check\|add\|rebuild` | Ingest dedup by content hash |

`wiki_search.py` is fully local: BM25 over an SQLite FTS5 index (title, heading, tags/aliases, body; stemmed, prefix-matched, alias-expanded from `index.md`). No network, no models. It matches words, not meaning, so add synonyms to the `## Aliases` table when a query misses. The index re-syncs changed pages on every call. If `python3` fails, fall back to grep.

---

## Query Workflow

Trigger: `wiki query: <question>` or "ask the wiki: <question>".

### Grounding Rule (strict)

Answer ONLY from pages under `wiki/` (sources/, entities/, concepts/, syntheses/, overview.md).

- Do NOT use general/training knowledge to fill gaps, even if you "know" the answer.
- Do NOT read files outside `wiki/` (rest of the vault, web) to answer.
- Every factual claim must carry a `[[PageName]]` citation. A claim you can't cite gets cut.
- If the wiki has no relevant pages, reply exactly:
  "Not in the wiki. No pages cover <topic>. Run `ingest <file>` to add a source."
  and stop: no partial answer, no "generally speaking…".
- If the wiki covers it only partly, answer the covered part and list what's missing
  under `## Not covered by the wiki`.

### Steps

1. If `wiki/index.md` doesn't exist or has no entries, tell the user to `ingest` something first. Stop.
2. Run `wiki_search.py "<question key terms>" -k 10`. Pass the distinctive nouns, names and part
   numbers, not the whole sentence. Aliases are expanded automatically. Run a second search with
   different wording if the first misses part of the question. Do not read `wiki/index.md` for this
   step. (No Python → fall back to grepping the managed folders for the terms + their aliases.)
3. If the search returns no matches, or none of the hits relate to the question → give the
   "Not in the wiki" reply and stop (no save prompt).
4. Read pages in layers, max 10 pages total across all layers:
   a. **Synthesized layer first** — matching `concepts/`, `entities/` and `syntheses/` pages.
      These already combine several sources, so they usually answer the question directly.
   b. **Follow links one hop** — from those pages, collect the `[[wikilinks]]` and frontmatter
      `sources:` slugs that bear on the question, and read those `sources/` pages for detail and
      exact figures. Do not follow links from pages reached this way (one hop only).
   c. **Direct source matches** — read any remaining `sources/` hits from step 2 not already read.
   If the cap is reached, prefer pages most specific to the question and note any skipped
   candidates under `## Not covered by the wiki`.

   **Reading rules** (always apply):
   - **Rank before reading:** within each layer, read in search-result order (highest first).
   - **Read the matching section, not the whole page:** read the hit's line range
     (Read with `offset`=start, `limit`=end-start+1, path `wiki/<path>`). Read the full page if the
     section doesn't fully answer, or the claim depends on surrounding context. One-hop pages
     from 4b have no line range: run `wiki_search.py` with the question terms to find their
     section, or read them whole if short.
   - **Stop when answered:** the 10-page cap is a ceiling, not a target. Stop once every part
     of the question is answered with citations — but before stating an exact figure or quote,
     always read the `sources/` page it comes from (step 4b), even if a concept page already
     gave it.
5. Synthesize an answer using only content from those pages, citing inline with `[[PageName]]`;
   direct quotes no more than 125 characters. Before replying, drop any sentence without a citation.
6. Append `## Sources` listing every page referenced, and `## Not covered by the wiki` if there are gaps.
7. Ask whether to save the answer as `wiki/syntheses/<slug>.md`.
8. Append to `wiki/log.md`: `## [YYYY-MM-DD] query | <question summary>` (append ` | not-found` when step 3 stopped the query).

---

## Important Notes

1. Never modify files under `wiki/original_sources/`, and never touch the pre-existing loose files in `wiki/`.
2. `wiki/log.md` is append-only — never edit historical entries.
