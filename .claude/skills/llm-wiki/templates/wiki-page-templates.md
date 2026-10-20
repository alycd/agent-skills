# Wiki Page Templates

This document provides standard templates for the five page types in llm-wiki.

---

## 1. Source Page (Source Summary Page)

Path: `wiki/sources/<slug>.md`

```markdown
---
title: "Source Title"
type: source
tags: []
date: YYYY-MM-DD
source_file: raw/<topic>/<filename>
source_type: pdf | docx | pptx | xlsx | markdown | image
last_updated: YYYY-MM-DD
---

## Summary
2-4 sentence comprehensive summary describing the document's core claims and value.

## Key Claims
- Point 1
- Point 2
- Point 3

## Key Quotes / Key Data
> "Direct quote content" — Context description (no more than 125 characters)

## Connections
- [[EntityName]] — Connection reason
- [[ConceptName]] — Connection type

## Contradictions
- Conflicts with [[OtherPage]] on: specific description
```

---

## 2. Article / Concept / Entity Page (Knowledge Pages)

Path: `wiki/concepts/<Name>.md` or `wiki/entities/<Name>.md`

```markdown
---
title: "Page Title"
type: concept | entity
tags: []
sources: [slug-1, slug-2]
last_updated: YYYY-MM-DD
---

## Overview
2-4 sentence overview synthesizing core understanding from all sources. Don't copy sources verbatim, reorganize and express.

## Main Content Sections (organized by topic, not by source)

### Subtopic One
...

### Subtopic Two
...

## See Also
- [[RelatedConcept]] — Connection reason (same topic)
- [[../other-topic/AnotherConcept]] — Connection reason (cross-topic)
```

---

## 3. Index Page (Directory Page)

Path: `wiki/index.md`

```markdown
# Wiki Index

_Last updated: YYYY-MM-DD_

## <Topic Name>

> One-sentence description of this topic

| Article | Summary | Updated |
|---|---|---|
| [[ArticleName]] | One-sentence summary | YYYY-MM-DD |
| [[AnotherArticle]] | One-sentence summary | YYYY-MM-DD |

## Sources

| Source | Type | Ingested |
|---|---|---|
| [[sources/slug-1]] | pdf | YYYY-MM-DD |
| [[sources/slug-2]] | markdown | YYYY-MM-DD |
```

---

## 4. Synthesis Page (Query Answer Archive Page)

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

Synthesized answer with `[[PageName]]` inline citations to wiki pages. Direct quotes no more than 125 characters.

## Sources

- [[sources/slug-1]] — Citation reason
- [[concepts/ConceptName]] — Citation reason

## Contradictions

- Conflicts with [[OtherPage]] on: specific description (omit this section if none)
```

---

## 5. Archive Page (Archived Page)

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

> **This page has been archived**, content has been superseded by [[NewPageName]] and will no longer update with source changes.

## Overview (Snapshot at time of archiving)
...

## See Also
- [[NewPageName]] — Current valid version
```

---

## Raw Source Template (Raw Material Archive)

Path: `raw/<topic>/<filename>` (original file, with optional frontmatter comment)

```
---
title: "Original Document Title"
url: https://... (if from web)
date: YYYY-MM-DD
author: Author Name
---

{Original content, unmodified}
```

> Files in `raw/` are **never modified**, this is the immutability foundation of the wiki system.
