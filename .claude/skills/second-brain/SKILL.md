---
name: second-brain
description: Relationship intelligence and conversation tracking system. Keeps per-person profiles with motivations, follow-ups, talking points, and key facts. Use when the user mentions a specific person's name and wants to update notes, see follow-ups, understand someone's motivations, check what to follow up on, mark something as done, or synthesize across all contacts. Triggers on phrases like "update my notes on X", "what should I follow up with X", "add to X's profile", "what do I know about X", "mark X as done", "show all open follow-ups", "import notes from this file", or any request about a named individual in a relationship/professional context.
---

# Second Brain — Relationship Intelligence

Tracks conversations, motivations, follow-ups, and persuasion context per person. Data lives in `~/.claude/second-brain/`.

## File format

Each person has a file at `~/.claude/second-brain/{first-last}.md` (lowercase, hyphenated). Example: `john-smith.md`.

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
2. **Find their file**: `~/.claude/second-brain/{name}.md`. Use Glob to list all files if unsure of exact filename.
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

1. Glob all files in `~/.claude/second-brain/*.md`.
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

1. Glob all files in `~/.claude/second-brain/*.md` and read each one fully.
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
