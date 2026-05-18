---
name: sprint-to-jira
description: Generate agile user stories and bulk-create Jira tickets from a sprint planning markdown file's Feature Summary table. Use when given a sprint doc and asked to create Jira tickets, generate stories for sprint features, or run the sprint-to-jira pipeline. Triggers on phrases like "create jira tickets for sprint", "generate stories from sprint doc", "make tickets for each feature", or "foreach item in sprint".
---

# Sprint → Jira Ticket Pipeline

Reads a sprint planning markdown file, generates an agile user story (JSON) for each row in the Feature Summary table, and creates a Jira ticket for each one via `create_jira_ticket.sh`.

## Instructions

### Step 1: Locate inputs

1. Identify the sprint markdown file — use the file the user referenced or the current working directory.
2. Find `create_jira_ticket.sh`:
   ```bash
   find /Users/alysidi -name "create_jira_ticket.sh" 2>/dev/null | head -1
   ```
3. Confirm `JIRA_API_TOKEN` is set in the environment (the script checks for it).

### Step 2: Parse the Feature Summary table

Read the markdown file and extract every row from the **Feature Summary** table. For each row, capture:
- **Title** — column "Title"
- **Summary** — column "Summary"
- **BusinessContext** — column "Business Context" (may be empty)

### Step 3: Create a task list

Use `TaskCreate` to create one task per feature before processing any of them. Subject format:
```
Agile story + Jira ticket: <Title>
```

### Step 4: Process each feature sequentially

For each feature (one at a time — clipboard is shared):

1. **Mark task `in_progress`** with `TaskUpdate`.

2. **Generate agile story JSON** using the schema below. Infer missing fields from the title and summary. Use the `agile-story` skill's output format but extend it to match what `create_jira_ticket.sh` expects:

```json
{
  "Topic": "<Title>",
  "Story": "As a <persona>, I want <capability> so that <outcome>.",
  "BusinessContext": "<business context from table or inferred>",
  "Criteria": "Given <precondition>, when <action>, then <expected result>. (repeat for each scenario)",
  "Details": {
    "users": "<who uses this feature>",
    "purpose": "<why it exists>",
    "constraints": "<known limits or rules>",
    "success_criteria": "<measurable outcomes>"
  }
}
```

3. **Write JSON to a temp file**:
   ```bash
   # Use index N (1-based) to avoid clipboard collisions
   /tmp/story_N.json
   ```

4. **Run the pipeline**:
   ```bash
   cat /tmp/story_N.json | pbcopy && pbpaste | /path/to/create_jira_ticket.sh
   ```

5. **Check the response** — a `201` HTTP status and a JSON body with `"key"` (e.g. `MAR-12444`) indicates success.

6. **Mark task `completed`** with `TaskUpdate`.

### Step 5: Report results

After all features are processed, output a markdown table:

| Feature | Jira Ticket |
|---------|-------------|
| Tours for New Features | MAR-12444 |
| ... | ... |

## JSON field guidance

| Field | Required | Notes |
|-------|----------|-------|
| `Topic` | Yes | Becomes the Jira ticket summary |
| `Story` | Yes | Classic "As a… I want… so that…" format |
| `BusinessContext` | No | Use table value; infer if blank |
| `Criteria` | Yes | Given/When/Then; one sentence per scenario |
| `Details.users` | No | Who interacts with this feature |
| `Details.purpose` | No | The "why" |
| `Details.constraints` | No | Technical or business limits |
| `Details.success_criteria` | No | Measurable outcomes |

## Edge cases

- **Empty Business Context**: Infer from the title and summary rather than leaving blank.
- **Script not found**: Run the `find` command in Step 1 and report the path to the user before proceeding.
- **Missing `JIRA_API_TOKEN`**: Inform the user and halt — do not attempt to create tickets.
- **Non-201 response**: Log the error, mark the task as still `in_progress`, and continue with remaining features. Report failures at the end.
- **Table not found**: Inform the user that no Feature Summary table was found in the file and ask them to point to the correct section.

## Requirements

- `jq` must be installed (`brew install jq`)
- `JIRA_API_TOKEN` environment variable must be set
- `create_jira_ticket.sh` must be executable and reachable
- macOS clipboard tools (`pbcopy`, `pbpaste`) must be available
