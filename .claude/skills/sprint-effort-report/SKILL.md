---
name: sprint-effort-report
description: Generate a per-assignee effort summary from a Jira sprint CSV export. Use when the user provides a sprint CSV file (e.g. s144.csv, sprint export) and wants to summarize effort by assignee, see who helped on cross-team subtasks, or understand sprint load distribution. Produces a new markdown report file.
---

# Sprint Effort Report

Generates a per-assignee effort breakdown from a Jira sprint CSV and writes a new markdown report file in the same directory as the CSV.

## CSV format

Expected columns (order matters):
```
Parent Key, Parent Summary, Key, Type, Summary, Status, Assignee, Impact, Effort, Created, Updated
```

The `Effort` column contains size values: `Small`, `Medium`, `Large`, `Extra-Large` (or blank).

## Rules

1. **Only count items with Status = "Done".** Any other status → excluded from all counts.
2. **Only count items that have an Effort value.** Blank effort → excluded from all counts.
3. **Count all non-Sub-task types** (Story, Task, Feature, Bug, Template, Epic, etc.) for their assigned person.
4. **Sub-tasks**: only count toward the subtask's assignee if that assignee **differs** from the parent story/task's assignee.
   - To find the parent's assignee: look up the Parent Key in the same CSV and read its Assignee column.
   - If the parent does not appear as its own row in the CSV, treat it as unknown — count the subtask.
5. **Unassigned** items are always excluded.
6. **Effort buckets**: Extra-Large, Large, Medium, Small (no "no size" bucket — those are dropped).
7. **Effort weights** for the weighted total: Extra-Large = 8, Large = 5, Medium = 3, Small = 1.

## Instructions

### Step 1 — Read the CSV

Read the full CSV file. Build two lookup maps:
- `row_by_key`: key → full row (for parent lookups)
- `assignee_by_key`: key → assignee (for quick parent owner checks)

### Step 2 — Classify each row

For each row:
- Skip if `Status` is not "Done"
- Skip if `Assignee` is blank or "Unassigned"
- Skip if `Effort` is blank
- If `Type` == "Sub-task":
  - Look up parent assignee via `Parent Key`
  - If parent assignee == row assignee → **skip**
  - If parent assignee != row assignee (or parent not found) → **count** for row assignee, mark as cross-assigned
- All other types → **count** for row assignee

### Step 3 — Build per-assignee buckets

For each qualifying row, add to the assignee's size bucket:
```
assignee → { Extra-Large: [], Large: [], Medium: [], Small: [] }
```

Compute the weighted total per assignee:
```
weighted_total = (count(Extra-Large) × 8) + (count(Large) × 5) + (count(Medium) × 3) + (count(Small) × 1)
```

Track cross-assigned subtasks separately for the cross-help section.

### Step 4 — Write the report

Create a new file named `<csv-basename>-effort-summary.md` in the same directory as the CSV.

#### Report structure

```markdown
# Sprint XXX — Effort Summary by Assignee

> Rules: only Done items are included. Items without effort are excluded.
> Sub-tasks only counted when assignee differs from parent owner.

## Summary Table

| Assignee | Extra-Large | Large | Medium | Small | Weighted Total |
| -------- | :---------: | :---: | :----: | :---: | :------------: |
| ...      |             |       |        |       |                |

Weights: XL=8, L=5, M=3, S=1. Sort by Weighted Total descending.

---

## Breakdown by Assignee

One section per assignee (order matches summary table):

### Name (N)

| Key | Type | Summary | Size | Note |
|-----|------|---------|------|------|
| ... | ...  | ...     | ...  | "cross-assigned from MAR-XXXX (Owner)" if subtask |

---

## Cross-Help Summary

List every parent that had at least one cross-assigned subtask.
For each such parent, show:

- **MAR-XXXX** _(Type, Parent Owner)_ — Parent Summary
  - MAR-YYYY (Sub-task, Assignee) → counted for **Assignee** as Size
  - MAR-ZZZZ (Sub-task, SameAsParent) → same as parent owner → skipped
```

## Example cross-help entry

```
- **MAR-12301** _(Story, Rajab Nagori)_ — Account Audience Summary Breakdown by ISP (Phase 1)
  - MAR-12335 (Sub-task, Rrahul Raja) → counted for **Rrahul Raja** as Medium
  - MAR-12313 (Sub-task, Rrahul Raja) → counted for **Rrahul Raja** as Small
  - MAR-12329 (Sub-task, Rajab Nagori) → same as parent owner → skipped
```

Only include parents that have at least one cross-assigned subtask with effort.
Still show the skipped same-owner subtasks for context (even without effort).
