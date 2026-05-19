---
name: second-brain
description: Relationship intelligence and conversation tracking system. Keeps per-person profiles with motivations, follow-ups, talking points, and key facts. Use when the user mentions a specific person's name and wants to update notes, see follow-ups, understand someone's motivations, check what to follow up on, mark something as done, or synthesize across all contacts. Also use for daily prioritization and log summaries by date range. Triggers on "daily summary", "what should I work on today", "morning briefing", "prioritize my day", "what's outstanding", "log for X this week", "what happened last week", "catch me up on X", or any request about a named individual in a relationship/professional context.
---

# Second Brain — Relationship Intelligence

Data lives in `/Users/alysidi/git/naqi/vault/Naqi/second_brain/{first-last}.md` (lowercase, hyphenated).

## File format

```markdown
---
name: Full Name
last-updated: YYYY-MM-DD
---
## Motivation
## How to Frame Conversations
## Open Follow-ups
- [ ] Item (added YYYY-MM-DD)
## Completed
- [x] Item (completed YYYY-MM-DD)
## Key Facts
## Interaction Log
### YYYY-MM-DD
Notes.
```

## On any request

1. Identify the person (or "everyone" for cross-person commands).
2. Find `{name}.md`; glob to confirm filename; create from template if missing.
3. Perform the action below.
4. After any write: show updated Open Follow-ups + Motivation.

---

### View profile
Output: Name, Motivation (1 paragraph synthesis), How to Frame (bullets), Open Follow-ups, Key Facts.

---

### Add notes
Route to the right section:
- Goals/values → **Motivation**
- Communication style → **How to Frame Conversations**
- Task/ask → **Open Follow-ups** (`- [ ] item (added DATE)`)
- Fact → **Key Facts**
- Conversation recap → **Interaction Log** (`### DATE` heading; append to today's entry if one exists)

Update `last-updated`.

---

### Mark done
Move matching `- [ ]` from Open Follow-ups to Completed as `- [x] ... (completed DATE)`.

---

### Lint
Glob all `*.md`. Fix mismatches:
- `[x]` in Open Follow-ups → move to Completed (keep existing ✅ date if present, else use `completed DATE`)
- `[ ]` in Completed → move to Open Follow-ups (restore `added DATE` or use today)

Update `last-updated` on changed files. Report as `| Person | Item | Action |` table. If nothing moved, say so.

---

### Dashboard
Glob all `*.md`. Extract Open Follow-ups. Output `| Person | Follow-up | Added |` table, oldest first.

---

### Consensus
Glob all `*.md`. Read fully. Synthesize across Motivation + Key Facts:
- **Where they agree** — shared themes/goals
- **Where they diverge** — opposing views or priorities
- **How to build alignment** — shared framing that bridges differences

Filter to topic if given.

---

### Understand motivation
Load person's profile. Output: what they care about most, what framing resonates, relevant open follow-ups. Tailor to topic if given.

---

### Import from file
Read file. Ask who it's about if unclear. Map content to correct sections. Merge (append/deduplicate — never overwrite). Show resulting profile.

---

### Log Summary by Date Range
Triggers: "log for X this week", "what happened last week", "catch me up on X", "weekly summary", "summarize my week"

**Resolve date range:**
| Expression | Range |
|------------|-------|
| today / yesterday | single day |
| this week | Mon → today |
| last week | prev Mon → prev Sun |
| last N days | today−N → today |
| this/last month | calendar month |

**Scope:** named person → one file; no person named → all files.

**Collect within range:** Interaction Log entries (by `### DATE`), completed items (by `completed DATE`), follow-ups added (by `added DATE`).

**Output:** narrative summary — what happened, completed, new follow-ups created, still open. If log is sparse, synthesize from follow-up activity. If no data at all, say so explicitly.

Format (single person): `## [Name] — Log Summary: [Period]` with **What happened / Completed / New follow-ups / Still open** sections.

Format (all people): `## Weekly Log Summary — [Period]` with a `### [Person]` block per person, closing totals line.

---

### Daily Summary
Triggers: "daily summary", "morning briefing", "what should I work on today", "what's my focus", "prioritize my day"

Glob all `*.md`. Collect all `[ ]` items with `added DATE`. Calculate age in days. Classify:

| Tier | Criteria |
|------|----------|
| 🔴 Critical | Age ≥ 7d OR time-pressure keywords: today, tomorrow, this week, by DATE, urgent, asap, named event |
| 🟠 High | Age 3–6d OR near-term deliverable / dependency blocking other work |
| 🟡 Normal | Age 1–2d |
| 🟢 New | Age 0d |

Sort oldest-first within each tier. Skip empty tiers. Output each tier as `| Person | Follow-up | Added | Age |` table. Close with total count and **Suggested focus** (1–2 sentences using Key Facts/Motivation context — not a restatement of the list).

---

## Key behaviors
- **Append/merge only** — never overwrite existing content.
- **Show a summary after every write** — not just "done."
- **Infer person from context** — "her" = last discussed person.
- **Date every entry** — follow-ups and log entries always get today's date.
- **Motivation ≠ Framing** — Motivation is WHO they are; Framing is HOW to talk to them.
- **Prompt if Motivation is empty** — ask what drives them before guessing at persuasion strategy.
