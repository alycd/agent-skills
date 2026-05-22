---
name: sprint-goals
description: Transform a Jira sprint CSV export into sprint goals for company-wide communication. Generates a Feature Summary table and a Slack-ready sprint goals post grouped by epic. Use when given a CSV file with Jira sprint tickets and asked to create sprint goals, generate a sprint summary, write the Slack sprint update, produce company-wide sprint communication, or make a sprint goals document. Trigger phrases: "create sprint goals", "generate sprint summary", "write slack sprint update", "make sprint goals from csv", "sprint goals from jira", "disseminate sprint", "sprint goals for the company".
---

# Sprint Goals

Transforms a Jira sprint CSV into two communication artifacts:
1. A **Feature Summary table** for Obsidian (the sprint planning doc)
2. A **Slack Summary** for company-wide sprint announcement

## Input

A CSV file exported from Jira with columns:
`Parent Key, Parent Summary, Key, Type, Summary, Status, Assignee, Impact, Effort, Created, Updated`

Also requires: the **sprint number** (e.g. 147).

## Instructions

### Step 1: Gather inputs

If the user hasn't provided a CSV file path, ask for it. If they haven't specified the sprint number, infer it from the filename (e.g., `sprint_147_jira.csv` → sprint 147) or ask.

### Step 2: Read and parse the CSV

Read the CSV file. Build a list of **features** by:

1. **Skip sub-tasks**: If a row has a non-empty `Parent Summary`, it is a sub-task. Don't create a separate feature entry — it will be represented by its parent row.
2. **Identify top-level tickets**: Rows where `Parent Key` and `Parent Summary` are both empty are standalone features. Use their `Summary` as the feature title.
3. **Identify epic-child tickets**: Rows where `Parent Summary` is set but the row itself is not a sub-task (Type = Story, Feature, Task, Bug) — use the row's `Summary` as the feature title and its `Parent Summary` as a hint for grouping.
4. **Skip total/empty rows**: Ignore the "Total: N items" row and blank rows.
5. **Skip purely operational tasks** that are not meaningful to external stakeholders, such as:
   - "Add New Major Account: X" (internal onboarding ops)
   - ISP-specific delivery investigations
   - Internal infrastructure ops with no user-facing impact

### Step 3: Group features by epic

Assign each feature to a **display epic** using these rules (in priority order):

1. If the ticket's `Parent Summary` maps to a known tinyEmail epic, use it — but apply the clean display name:
   - `Authenticator Implementation` → `Authenticator`
   - `Adaptive Traffic Shaping` → `Adaptive Traffic Shaping`
   - `User Action Audit` → `User Action Audit`
   - `SamCart Integration` → `3rd Party Integrations`
   - `Customer Support Request` → `Customer Support`
2. If the ticket has no parent, infer the epic from the ticket summary using context clues:
   - SMS, Voizee → `SMS`
   - Onboarding, Chatbot, Tours → `Onboarding` or `New Feature Utilization`
   - Segment, Audience, List, Contact → `Audience`
   - Campaign Link, Link Retention, Replay Attack → `Campaign Links`
   - Nightly AI, Dashboard, Analytics, Engagement → `Analytics`
   - Relay, API Key, List Cleaning → `tinyEmail and APIs`
   - Billing, Stripe, Invoice → `Customer Support` (or `Billing`)
   - HMAC, Security → `Campaign Links` (or `Security`)
   - A/B Test → `Campaigns`
   - Pause Integration, Discount, 3rd party → `3rd Party Integrations`
   - Workflow Node, Template Preview, BO (Back Office) → `Customer Support`
3. For anything that doesn't fit, use your best judgment to assign a logical epic name.

### Step 4: Generate descriptions

For each feature, produce:

- **Summary** (for the table): A 1–2 sentence neutral description of what the feature does. Technical but accessible. Present tense. No "we" or "users can" framing — state what the feature does: "Generates per-account HMAC signatures for tracked campaign links to ensure integrity."
- **Business Context** (for the table): 1 sentence on the business or customer value. Why it matters. Start with a verb or noun — no "This feature...". Example: "Protects click metric integrity; required for compliance and trust in click tracking."
- **Slack description**: 1 sentence, active voice, customer-facing impact. What does this mean for users? Start with a strong verb. Example: "Extends campaign link engagement data retention past the 30-day limit on a per-user basis for longer attribution windows."

Use your knowledge of tinyEmail's product domain to write accurate, non-generic descriptions. GreenArrow is the email delivery infrastructure. tinyAlbert is an AI-powered email product. Back Office (BO) is the internal admin tool. Entri handles DNS. Prometheus is used for infrastructure monitoring.

### Step 5: Map effort to size

| Effort value | Size |
|---|---|
| Small | S |
| Medium | M |
| Large | L |
| Extra-Large | XL |
| (empty) | — |

For features where multiple sub-tasks contribute, use the parent story's `Effort` if available.

### Step 6: Generate the Feature Summary table

Output a Markdown table with these columns: `Epic | Title | Summary | Business Context | Size`

Sort rows by epic (group all rows of the same epic together). Use the same epic ordering as Sprint 146:
New Feature Utilization → Onboarding → 3rd Party Integrations → Audience → Campaign Links → User Action Audit → Authenticator → Adaptive Traffic Shaping → Customer Support → Analytics → tinyEmail and APIs → SMS

Example row:
```
| Campaign Links | Stop Replay Attacks on Campaign Links | Detects and blocks replay attacks on campaign link tokens | Protects click metric integrity and deliverability reputation from malicious replay activity | L |
```

### Step 7: Generate the Slack Summary

Format for Slack (Slack uses `*bold*` and `_italic_` markdown):

```
*Sprint [N] — What We're Building*

*[Epic Name]*
• *[Feature Title]* — [Slack description sentence.]

*[Next Epic Name]*
• *[Feature Title]* — [Slack description sentence.]
...
```

- Use the same epic grouping and ordering as the table.
- Omit epics that have zero features.
- Each bullet starts with `•` (not `-`).
- The feature title in each bullet is bold: `*Feature Title*`.
- The description comes after ` — ` (space-dash-dash-space).

### Step 8: Write output to file

Write both artifacts to a Markdown file at:
`[parent_directory_of_csv]/Sprint [N].md`

If that file already exists, ask the user before overwriting.

Structure the file as:

```markdown
## Feature Summary

| Epic | Title | Summary | Business Context | Size |
|------|-------|---------|-----------------|------|
[rows]

---

## Slack Summary

[slack content]
```

### Step 9: Confirm

Tell the user the file was written and show a brief count: how many features were included, how many epics.

## Notes

- Don't include carry-over tracking, backlog items, or items already Done from the previous sprint unless they appear in the current CSV with significant new work remaining.
- If a ticket appears both as a parent row AND has sub-tasks, represent it as a single feature entry (don't duplicate).
- The Feature Summary table is the source of truth for sprint planning; the Slack Summary is for company-wide communication — keep the Slack descriptions punchy and non-technical.
- When in doubt about whether to include a ticket, include it rather than exclude it — the user can trim.
