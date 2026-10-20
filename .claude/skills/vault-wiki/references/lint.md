# wiki lint — Wiki Health Check (Deterministic Only)

Fast, no-LLM-pass health check for `wiki/`. Grep/Read only — no semantic analysis, so this stays cheap to run often.

**Trigger**: `wiki lint` or "check the wiki"

## Parameter

None. If `wiki/index.md` doesn't exist or has no entries, say so and stop (nothing to lint yet).

## Run

```bash
python3 .claude/skills/vault-wiki/scripts/wiki_lint.py
```

The script does checks 1-3 exactly. Check 4 is a heuristic candidate list (capitalised names in 3+ source pages, minus words also used in lowercase and names that already have a page or alias). Review it: keep real people/companies/products, drop generic acronyms and part numbers that belong on a concept page. If Python is unavailable, do the checks by hand with Grep/Read.

## Checks

1. **Orphaned pages** — pages under `sources/`, `entities/`, `concepts/`, `syntheses/` not referenced by any `[[wikilink]]` from another page, and not listed in `index.md`.
2. **Broken links** — `[[WikiLink]]` targets that don't correspond to an existing file.
3. **Index consistency** — entries in `wiki/index.md` whose target page doesn't actually exist.
4. **Missing entity pages** — proper nouns/entities referenced by name in 3+ source pages but with no standalone page under `wiki/entities/`.

Do **not** read full page bodies for semantic contradiction/staleness checking — that's out of scope for this fast lint (use `wiki query:` if you want a synthesized read of the current state).

## Output

Structured report grouped by check, most severe first (broken links > index inconsistency > orphans > missing entities). Ask whether to save it as `wiki/lint-report.md`. Append to `wiki/log.md`: `## [YYYY-MM-DD] lint | Wiki health check`.
