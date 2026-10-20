# ingest — Document Ingestion Command

Ingest a document into this vault's `wiki/` folder (multimodal support).

**Trigger**: `ingest <path>` or "add this to the wiki"

## Parameter

`$ARGUMENTS` is a file path — anywhere: inside the vault, or an external path (e.g. Downloads). Optional `--topic <slug>` is accepted only as a free-text hint for which section of `wiki/index.md` to file it under; it does not create subdirectories.

```
ingest PDFs/2026 Naqi Logix Investor Deck July.VFF2.pdf
ingest ~/Downloads/some-report.pdf
ingest Daily Notes/Jul-09-2026.md
```

### No Path Given — Scan `original_sources/`

If `ingest` is invoked with no path, treat `wiki/original_sources/` as the inbox: list its files, drop any that already have an `ingest` log entry in `wiki/log.md` (matched by filename), and process what's left.

- **Exactly one file left** — ingest it directly.
- **Multiple files left** — process them one at a time (batch), per the standard batch-ingestion notes below.
- **Nothing left** — say so; nothing to ingest.

## Supported Formats

`.md` `.txt` `.pdf` `.docx` `.pptx` `.xlsx` `.png` `.jpg` `.jpeg` `.webp`

## Execution Flow

### Step 0 — Dedup Check

Run `python3 .claude/skills/vault-wiki/scripts/wiki_manifest.py check "<path>"`:

- `new` → continue.
- `changed` → same filename, edited content: tell the user and re-ingest (overwrites the existing source page).
- `same` → already ingested: ask the user whether to force re-ingest; otherwise skip.
- `duplicate-of <file>` → identical content already ingested under another name: tell the user and skip unless they insist.

If the manifest doesn't exist yet, run `wiki_manifest.py rebuild` once first. If Python is unavailable, fall back to matching the filename against `ingest` entries in `wiki/log.md`.

### Step 1 — Original-Copy Rule

Determine whether the path is already inside this vault:

- **Inside the vault** (anywhere — `wiki/`, `PDFs/`, `Daily Notes/`, etc.): it's already the original. Do not copy it. `source_file` = its existing vault-relative path.
- **Outside the vault**: copy the file into `wiki/original_sources/<filename>` untouched (flat, no topic subdirectories). If a same-named file already exists there, ask whether to overwrite. `source_file` = `original_sources/<filename>`.

### Step 2 — Multimodal Content Extraction

| File Type | Method |
|---|---|
| `.md` `.txt` | Direct `Read` tool |
| `.pdf` | `pdfplumber` — text + tables |
| `.docx` | `python-docx` — body, headings, tables |
| `.pptx` | Per-slide title, body, notes |
| `.xlsx` `.csv` | `pandas` → Markdown tables |
| `.png` `.jpg` `.jpeg` `.webp` | `Read` tool directly (Claude vision) |

Unify to Markdown with heading hierarchy preserved.

### Step 3 — Wiki Write

1. Read `wiki/index.md` (and `wiki/overview.md` if it has content) for context.
2. Find related pages: run `wiki_search.py "<5-10 key names, part numbers and concepts from the document>" -k 8`,
   then read the hit sections of the 2-3 most relevant pages for cross-reference context (skip reading the
   full corpus — this is what keeps ingest fast). Entity/concept hits tell you which pages to update in step 5
   instead of creating duplicates.
3. Write `wiki/sources/<slug>.md` per the Source Page template.
4. Update `wiki/index.md` — append entry under the matching topic section (create the section if new).
5. Create/update relevant pages under `wiki/entities/` and `wiki/concepts/` — only for entities/concepts that are central to this document, not every passing mention.
6. **`overview.md`**: update only if this source meaningfully changes the cross-source synthesis (e.g. a new major topic, a correction to prior understanding). Routine/incremental ingests should skip this step entirely — note in the output summary that it was skipped.
7. If this source conflicts with an existing page's claims, annotate the conflict in that page's `## Contradictions` section before deciding whether to also update its body.
8. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <Title>`, then record the ingest:
   `wiki_manifest.py add "<original path>" <slug>` (the vault copy if one was made in Step 1).
   The search index picks up the new pages on its next run; no rebuild needed.
9. Output a short summary: pages created, pages updated, contradictions found, whether overview.md was touched.

## Notes

- Never modify a file already sitting under `wiki/original_sources/`.
- For batch ingestion, process one file at a time, logging after each.

## Conventions

**Naming**
- Source pages: `kebab-case.md`, slug derived from the original filename
- Entity pages: `TitleCase.md` (e.g. `Honsenn.md`)
- Concept pages: `TitleCase.md` (e.g. `D59.md`)
- Archive pages: keep original filename, move to `wiki/archive/`

**Contradictions** — annotate the conflict in the page's `## Contradictions` section before deciding whether to update its body; never silently overwrite.

**Archiving a page**
1. Move the file to `wiki/archive/`
2. Update referencing pages: `[[PageName]]` → `[[archive/PageName]]`, add an `[Archived]` tag
3. Append log: `## [YYYY-MM-DD] archive | <PageName>`

Archive is a snapshot — it does not update after archiving.

**Interruption recovery** — `wiki/log.md` is the source of truth:
- Log has an `ingest` entry and the manifest has the file → completed normally
- Log entry but no manifest entry → interrupted after logging; run `wiki_manifest.py add`
- `wiki/sources/<slug>.md` exists, no log entry → interrupted before logging; re-run `ingest <path>`
- Neither exists → never started or failed early

Re-running overwrites existing pages with the latest version; it does not duplicate them.
