# Vault Wiki Page Templates

## 1. Source Page

Path: `wiki/sources/<slug>.md`

```markdown
---
title: "Source Title"
type: source
tags: []
date: YYYY-MM-DD
source_file: original_sources/<filename> | <original in-vault path>
source_type: pdf | docx | pptx | xlsx | markdown | image
last_updated: YYYY-MM-DD
---

## Summary
2-4 sentence comprehensive summary describing the document's core claims and value.

## Key Claims
- Point 1
- Point 2

## Key Quotes / Key Data
> "Direct quote content" — Context description (no more than 125 characters)

## Connections
- [[EntityName]] — Connection reason
- [[ConceptName]] — Connection type

## Contradictions
- Conflicts with [[OtherPage]] on: specific description
```

---

## 2. Entity / Concept Page

Path: `wiki/entities/<Name>.md` or `wiki/concepts/<Name>.md`

```markdown
---
title: "Page Title"
type: entity | concept
tags: []
sources: [slug-1, slug-2]
last_updated: YYYY-MM-DD
---

## Overview
2-4 sentence overview synthesizing understanding across all sources. Reorganize and express — don't copy sources verbatim.

### Subtopic One
...

## See Also
- [[RelatedPage]] — Connection reason
```

---

## 3. Index Page

Path: `wiki/index.md`

```markdown
# Wiki Index

_Last updated: YYYY-MM-DD_

## <Topic Name>

> One-sentence description of this topic

| Article | Summary | Updated |
|---|---|---|
| [[ArticleName]] | One-sentence summary | YYYY-MM-DD |

## Sources

| Source | Type | Ingested |
|---|---|---|
| [[sources/slug-1]] | pdf | YYYY-MM-DD |
```

---

## 4. Synthesis Page (saved query answer)

Path: `wiki/syntheses/<slug>.md`

```markdown
---
title: "Question Summary"
type: synthesis
tags: []
sources: [slug-1, slug-2]
query_date: YYYY-MM-DD
last_updated: YYYY-MM-DD
---

## Question
The complete query question.

## Answer
Synthesized answer with `[[PageName]]` inline citations. Direct quotes no more than 125 characters.

## Sources
- [[sources/slug-1]] — Citation reason

## Contradictions
- Conflicts with [[OtherPage]] on: ... (omit if none)
```

---

## 5. Archive Page

Path: `wiki/archive/<original-name>.md`

```markdown
---
title: "Original Page Title [Archived]"
type: source | concept | entity
archived_date: YYYY-MM-DD
superseded_by: "[[NewPageName]]"
sources: []
last_updated: YYYY-MM-DD
---

> **This page has been archived**, content superseded by [[NewPageName]], no longer updates with source changes.

## Overview (Snapshot at time of archiving)
...

## See Also
- [[NewPageName]] — Current valid version
```
