# wiki-ingest — Document Ingestion Command

Ingest documents into LLM Wiki knowledge base (multimodal support).

**Trigger**: `wiki-ingest <file>` or `把 <file> 加入 wiki`

## Parameter

`$ARGUMENTS` is the file path under `raw/` directory, for example:

```
wiki-ingest raw/papers/attention-is-all-you-need.pdf
wiki-ingest raw/slides/q1-review.pptx
wiki-ingest raw/reports/market-analysis.xlsx
wiki-ingest raw/articles/my-article.md
```

## Supported Formats

`.md` `.txt` `.pdf` `.docx` `.pptx` `.xlsx` `.png` `.jpg` `.jpeg` `.webp`

## Execution Flow

Execute strictly according to **Ingest Workflow** in SKILL.md:

### Step -1 — Determine WIKI_ROOT

Parse workspace path in priority order (command-line `@<path>` → `.claude/config/llm-wiki.json` → cwd), expand `~` to absolute path. If directory doesn't exist, auto-create complete directory structure then continue. All subsequent paths are relative to WIKI_ROOT.

### Step 0 — Deduplication Check

Read `wiki/log.md`, check by filename if there's already an ingest record. If exists, ask user whether to force re-ingest, otherwise skip.

### Step 1 — Multimodal Content Extraction

Choose extraction method based on file extension:

| File Type | Extraction Method |
|---|---|
| `.md` `.txt` `.json` `.yaml` | Direct Read tool |
| `.pdf` | Use pdfplumber to extract text and tables (see pdf skill) |
| `.docx` | Use python-docx to extract body, headings, tables (see docx skill) |
| `.pptx` | Extract each slide's title, body, notes (see pptx skill) |
| `.xlsx` `.csv` | Use pandas to convert to Markdown tables (see xlsx skill) |
| `.png` `.jpg` `.jpeg` `.webp` | Use Read tool to read image directly (Claude vision) |

Extraction result is unified to Markdown text with heading hierarchy.

### Step 2-10 — Wiki Write (Execute in Order)

1. Read `wiki/index.md` and `wiki/overview.md` to get current context
2. Read recent 5 source pages to establish cross-reference context
3. Write `wiki/sources/<slug>.md` (Source Page Format, see [../templates/wiki-page-templates.md](../templates/wiki-page-templates.md))
4. Update `wiki/index.md`, append new entry in corresponding topic section
5. Update `wiki/overview.md`, revise cross-source synthesis summary
6. Create/update key entity pages under `wiki/entities/`
7. Create/update key concept pages under `wiki/concepts/`
8. Mark contradictions with existing wiki content (write to related pages' `## Contradictions` section)
9. Append log to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <Title>`
10. Output summary: which pages created, which updated, which contradictions found

## Notes

- **Never modify** raw documents in `raw/`
- Contradiction annotation takes priority over content overwrite: annotate first, then decide whether to update
- For batch ingestion, process files one by one, append one log entry after each file completes
- Page templates see [../templates/wiki-page-templates.md](../templates/wiki-page-templates.md)
