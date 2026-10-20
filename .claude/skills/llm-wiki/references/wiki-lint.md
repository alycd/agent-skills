# wiki-lint — Wiki Quality Check Command

Check Wiki quality, find orphaned pages, broken links, contradictions and other issues.

**Trigger**: `wiki-lint` or `wiki 检查`

## Parameter

No parameters.

## Execution Flow

Execute according to **Lint Workflow** in SKILL.md (two phases):

**Step 0** — Parse WIKI_ROOT (`.claude/config/llm-wiki.json` → cwd), all paths based on WIKI_ROOT.

### Phase One — Deterministic Checks (Grep + Read)

1. **Orphaned pages** — Pages not referenced by any other page's `[[link]]`
2. **Broken links** — `[[WikiLink]]` pointing to non-existent pages
3. **Index consistency** — Whether pages listed in `wiki/index.md` actually exist
4. **Missing entity pages** — Entities mentioned in 3+ pages but without standalone pages

### Phase Two — Semantic Analysis (Claude reads max 20 page samples)

5. **Content contradictions** — Conflicting claims across pages
6. **Outdated summaries** — Pages not updated after newer source ingestion
7. **Underdeveloped concepts** — Thin concept pages referenced in many places
8. **Knowledge gaps** — Typical questions the wiki can't answer, suggest supplementing sources

## Output

Generate structured lint report, organized by category and severity. Ask user whether to save as `wiki/lint-report.md`.
Append log to `wiki/log.md`: `## [YYYY-MM-DD] lint | Wiki health check`
