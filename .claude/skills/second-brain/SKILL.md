---
name: second-brain
description: Relationship intelligence and conversation tracking system. Keeps per-person profiles with motivations, follow-ups, talking points, and key facts. Use when the user mentions a specific person's name and wants to update notes, see follow-ups, understand someone's motivations, check what to follow up on, mark something as done, or synthesize across all contacts. Also use for daily prioritization: triggers on "daily summary", "what should I work on today", "morning briefing", "prioritize my day", "what's outstanding". Triggers on phrases like "update my notes on X", "what should I follow up with X", "add to X's profile", "what do I know about X", "mark X as done", "show all open follow-ups", "import notes from this file", or any request about a named individual in a relationship/professional context.
---

# Second Brain — Relationship Intelligence

Tracks conversations, motivations, follow-ups, and persuasion context per person. Data lives in `/Users/alysidi/git/naqi/vault/Naqi/second_brain`.

## File format

Each person has a file at `/Users/alysidi/git/naqi/vault/Naqi/second_brain/{first-last}.md` (lowercase, hyphenated). Example: `john-smith.md`.

```markdown
---
name: Full Name
last-updated: YYYY-MM-DD
---

## Motivation
What drives this person: their goals, values, fears, incentives, and what they care about most.

## How to Frame Conversations
Key context for persuasion and alignment — what resonates, what to avoid, their communication style.

## Open Follow-ups
- [ ] Item to follow up on (added YYYY-MM-DD)
- [ ] Another pending item

## Completed
- [x] Thing that was done (completed YYYY-MM-DD)

## Key Facts
- Important things to remember (role, company, context)

## Interaction Log
### YYYY-MM-DD
Notes from a specific conversation or meeting.
```

## Instructions

### On any person-related request

1. **Identify the person** from the user's message (name, nickname, or "him/her" if clear from context).
2. **Find their file**: `/Users/alysidi/git/naqi/vault/Naqi/second_brain/{name}.md`. Use Glob to list all files if unsure of exact filename.
3. **If file doesn't exist**, create it with the template above before proceeding.
4. **Perform the requested action** from the list below.
5. **Always show the updated "Open Follow-ups + Motivation" view** after any write operation.

---

### Action: View a person's profile

Show a formatted summary:

```
## [Name] — Profile Summary

**Motivation:** [one-paragraph synthesis from the Motivation section]

**How to frame your next conversation:**
[bullet points from "How to Frame Conversations"]

**Open Follow-ups:**
- [ ] item (added DATE)
- [ ] item (added DATE)

**Key Facts:**
- fact
```

---

### Action: Add notes or update a section

When the user says "add to X's profile", "remember that X said...", "note that X cares about...", "X mentioned...":

1. Determine which section the information belongs to:
   - Motivation/values/goals → **Motivation**
   - Communication style, what resonates → **How to Frame Conversations**
   - Something to do or ask → **Open Follow-ups** (add `- [ ] item (added DATE)`)
   - General fact → **Key Facts**
   - Conversation recap → **Interaction Log** (under today's date heading)
2. Edit the file to add the information in the correct section.
3. Update `last-updated` in frontmatter.

---

### Action: Mark a follow-up as done

When the user says "mark X as done", "checked off X", "completed X", "X is done":

1. Find the matching `- [ ]` item in **Open Follow-ups**.
2. Move it to **Completed** and change `[ ]` to `[x]`, appending `(completed DATE)`.
3. Confirm which item was checked off.

---


### Action: Lint follow-ups

When the user says "lint followups", "complete followups", "sync followups", or "clean up followups":

1. Glob all files in `/Users/alysidi/git/naqi/vault/Naqi/second_brain/*.md`.
2. For each file, read the **Open Follow-ups** and **Completed** sections.
3. Fix mismatches:
   - `[x]` item found in **Open Follow-ups** → remove from Open Follow-ups, append to **Completed** preserving the text (replace `added DATE` with `completed DATE` or keep the existing ✅ date if present)
   - `[ ]` item found in **Completed** → remove from Completed, append to **Open Follow-ups** (keep original text, restore `added` date if visible, or use today's date)
4. Update `last-updated` frontmatter for any file that changed.
5. Report a summary of every move made:

```
## Lint Results

| Person | Item | Action |
|--------|------|--------|
| Rodney | Review AI roadmap | Open Follow-ups → Completed |
| John   | Send proposal     | Completed → Open Follow-ups |
```

If nothing needed moving, report "All follow-ups are consistent — nothing to move."

---

### Action: Import from a markdown file

When the user provides a file path or pastes content from an existing notes file:

1. Read the file.
2. Ask: "Which person is this about?" if not obvious.
3. Parse the content and map it to the correct sections of that person's profile.
4. Merge with any existing profile (don't overwrite — append new facts, deduplicate follow-ups).
5. Show the resulting profile summary.

---

### Action: Synthesize across all people

When the user says "show all open follow-ups", "who do I need to follow up with", "give me a dashboard", or "what's pending":

1. Glob all files in `/Users/alysidi/git/naqi/vault/Naqi/second_brain/*.md`.
2. For each file, extract the **Open Follow-ups** section.
3. Output a consolidated table:

```
## Follow-up Dashboard

| Person | Follow-up | Added |
|--------|-----------|-------|
| John Smith | Send proposal draft | 2026-05-10 |
| Sarah Lee | Ask about budget timeline | 2026-05-15 |
```

4. Group by urgency if dates suggest it (oldest first).

---

### Action: Consensus synthesis across people

When the user asks "what do people agree on", "find consensus", "where do they align", "what's the common thread", or "scan everyone on [topic]":

1. Glob all files in `/Users/alysidi/git/naqi/vault/Naqi/second_brain/*.md` and read each one fully.
2. Extract Motivation, Key Facts, and any relevant notes per person.
3. Identify:
   - **Points of agreement** — shared themes, overlapping goals, similar product/strategy opinions
   - **Points of divergence** — where motivations or opinions differ
   - **Alignment opportunities** — what framing could bring divergent people into agreement
4. Output a consensus report:

```
## Consensus Report — [Topic or "All People"]

**Where they agree:**
- Shared theme or belief (held by Person A, Person B)

**Where they diverge:**
- Point of difference: Person A thinks X, Person B thinks Y

**How to build alignment:**
- Frame the discussion around [shared value] to bring both sides together
```

5. If a specific topic was given (e.g., "consensus on the product roadmap"), filter synthesis to facts and motivations relevant to that topic.

---

### Action: Understand someone's motivation

When the user asks "how should I approach X", "how do I persuade X", "what does X care about", "how should I frame this to X":

1. Load the person's profile.
2. Synthesize a **conversation brief**:
   - What they care about most (from Motivation)
   - What framing resonates (from How to Frame)
   - Any relevant open follow-ups to reference
3. Tailor it to the specific topic if the user provided one.

---

### Action: Daily Summary

When the user says "daily summary", "what should I work on today", "morning briefing", "what's outstanding", "prioritize my day", "daily brief", or "what's my focus today":

1. Glob all files in `/Users/alysidi/git/naqi/vault/Naqi/second_brain/*.md` and read each one fully.
2. Collect every open `- [ ]` item across all files, noting the person's name and the `added YYYY-MM-DD` date.
3. Calculate the **age** of each item in days from today's date.
4. Classify each item into a priority tier:

   | Tier | Label | Criteria |
   |------|-------|----------|
   | 🔴 | **Critical** | Age ≥ 7 days (stale/overdue) OR contains time-pressure keywords: "today", "tomorrow", "this week", "before [date]", "by [date]", "urgent", "asap", or a named upcoming event (e.g. "Viva Tech", "CES", "Beyond Expo", "launch") |
   | 🟠 | **High** | Age 3–6 days OR references a near-term deliverable, meeting, or person dependency that blocks other work |
   | 🟡 | **Normal** | Age 1–2 days — active but not yet pressured |
   | 🟢 | **New** | Age 0 days — added today |

5. Within each tier, sort items oldest-first (highest age first).
6. Output the daily brief in this format:

```
## Daily Brief — YYYY-MM-DD

### 🔴 Critical
| Person | Follow-up | Added | Age |
|--------|-----------|-------|-----|
| Dave | Schedule 1.5hr session Thu/Fri | 2026-05-11 | 8d |

### 🟠 High
| Person | Follow-up | Added | Age |
|--------|-----------|-------|-----|
| Rodney | Create Git account for Rodney | 2026-05-15 | 4d |

### 🟡 Normal
| Person | Follow-up | Added | Age |
|--------|-----------|-------|-----|
| Dave | Review D59 documents | 2026-05-17 | 2d |

### 🟢 New (added today)
| Person | Follow-up | Added | Age |
|--------|-----------|-------|-----|
| Zavier | Write skateboard vs. ferrari doc | 2026-05-19 | 0d |

---
**Total open:** X items across Y people
**Suggested focus:** [1–2 sentence recommendation on where to spend energy today, based on Critical + High items and any visible dependencies or upcoming events]
```

7. If all items fall in Normal or New, note that there are no overdue items and suggest tackling the oldest Normal items first.
8. The **Suggested focus** line should synthesize context from Key Facts and Motivation sections — not just restate the list. For example: "Dave is expecting a session this week and has a Viva Tech deadline coming up — prioritize the scheduling item and D59 review."

---

## Key behaviors

- **Never overwrite** existing content — always append or merge.
- **Always show a summary** after writes, not just "done."
- **Infer the person** from context — if the user says "her" and the last person discussed was Sarah, use Sarah.
- **Prompt for missing info**: if the Motivation section is empty and the user asks how to persuade someone, ask what you know about what drives them before guessing.
- **Date every entry**: all follow-ups and log entries get today's date.
- **Keep Motivation and Framing separate**: Motivation is WHO they are; Framing is HOW to talk to them.

## Quick reference

| User says | Action |
|-----------|--------|
| "What do I know about X?" | View profile |
| "Add a follow-up for X" | Add to Open Follow-ups |
| "X mentioned they care about Y" | Update Motivation |
| "How should I approach X about Z?" | Motivation + Framing brief |
| "Mark X as done for John" | Move to Completed |
| "Import this file about Sarah" | Parse + merge into profile |
| "Who do I need to follow up with?" | Dashboard synthesis |
| "What's pending with everyone?" | Dashboard synthesis |
| "Find consensus on X" | Consensus synthesis |
| "Where do people agree?" | Consensus synthesis |
| "Scan everyone on [topic]" | Consensus synthesis |
| "Lint followups" / "complete followups" | Move mismatched checkboxes between Open Follow-ups and Completed |
| "Daily summary" / "What should I work on?" / "Morning briefing" | Priority-classified daily brief across all people |
