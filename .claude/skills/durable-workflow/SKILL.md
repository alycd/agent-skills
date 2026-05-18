---
name: durable-workflow
description: Create and run durable, parameterized workflows defined as DAGs, with auto or manual steps, dependency resolution, and optional retries.
version: 1.0.0
author: tinyJarvis
license: MIT
metadata:
  hermes:
    tags: [workflow, dag, automation, retries, skills, durable]
    related_skills: [software-development/cron-retry-rescheduler, software-development/dns-checker]
    category: software-development
---

# Durable Workflow

Manages durable, parameterized workflows for any entity type. Workflows are defined as DAGs — steps with no dependencies run in parallel, steps with dependencies wait on parents. Each step can invoke skills automatically or be completed manually. Steps can be configured to retry automatically after a delay if they fail.

See `references/cron-retry-repair.md` for the cronjob-based retry pattern and the missing-retry-job pitfall.
See `references/cron-retry-migration.md` for the Linux-crontab-to-Hermes migration note and verification checklist.
See `references/onboarding-auto-run-and-retry.md` for the onboarding-specific auto-run and self-rescheduling pattern observed in Beta Corp onboarding.
Use the `cron-retry-rescheduler` skill when a retry needs to be represented as a real cron job and verified in `cron list`.
See `references/cron-retry-alignment.md` for the one-job-per-step rule, stale-job cleanup, and verification pattern.
See `references/cron-retry-hygiene.md` for a concise session note on replacing stale retry jobs and verifying the active cron.

Pitfall: resolve workflow paths against the active user's HOME directory (for example, `/home/ubuntu` in headless runs). Do not assume `/root` or hardcode a home path when reading or writing `~/.claude/workflows/...`.

Pitfall: manually editing a workflow entity YAML to mark a step done does not itself trigger auto-advance. `auto_run_unblocked_steps` only applies when the workflow runner processes a step completion and re-evaluates the DAG.

See `references/polling-checker-pattern.md` for the Python checker + cron-reschedule pattern used for polling monitor steps.

## File locations

```text
~/.claude/workflows/
└── {workflow-name}/
    ├── workflow.yaml        # DAG definition
    ├── {entity-id}.yaml     # one file per entity instance
    └── {entity-id}.yaml
```

## workflow.yaml format

```yaml
name: workflow-name
entity_label: customer       # what the tracked entity is called: customer, product, partner, etc.
description: What this workflow does
auto_run_unblocked_steps: true|false  # optional; if true, newly unblocked auto steps run automatically

steps:
  - id: step_id              # snake_case, unique within this workflow
    name: Human-readable name
    description: What this step involves
    owner: team-or-person
    depends_on: []           # empty = parallel, starts immediately
    skills: [skill-a, skill-b]   # optional: skills to invoke when running this step
    retry:                   # optional: auto-retry config for steps that may fail transiently
      interval: 6h           # how long to wait before retrying (e.g. 30m, 6h, 1d)
      max_attempts: 5        # optional: omit for unlimited retries
    prompt: |                # optional: instructions, {entity.field} is interpolated
      Use skill-a to do X for {entity.name} with plan {entity.plan}.
      Then use skill-b to verify Y.
      If successful, complete this step. Otherwise report why and do not complete it.
```

**Dependency rules:**
- `depends_on: []` → immediately actionable when entity run starts
- `depends_on: [step_a, step_b]` → blocked until ALL listed steps are `done`
- `skipped` steps count as `done` for dependency resolution
- Steps without `skills`/`prompt` are manual-only

**Retry rules:**
- `retry` is optional — omit it for steps that should not auto-retry
- `interval` supports: `Xm` (minutes), `Xh` (hours), `Xd` (days)
- `max_attempts` is optional — omit for unlimited retries
- When a step with `retry` fails, status becomes `retry_scheduled` and `retry_at` is set
- Retry jobs are created with the native `cronjob` tool, not a separate `schedule` skill or Linux `crontab`
- Use the `cron-retry-rescheduler` skill when you need a reusable pattern for creating and verifying retry cron jobs
- If a legacy Linux crontab entry exists for the same retry, remove it so Hermes cronjob is the single scheduler path
- Keep `enabled_toolsets` for the retry job inclusive of `cronjob`, `terminal`, and `file` when the retry must both re-check DNS and rewrite workflow state
- When `retry_count` reaches `max_attempts`, no further retries are scheduled — step stays `in_progress` with failure notes
- For short polling retries such as `5m` / `5min`, prefer a small Python checker script that evaluates the exact pass/fail condition for the step and emits the state needed for scheduling. Feed that output into the `cron-retry-rescheduler` skill so the retry cron job is created and verified consistently.

## Entity instance file format (`{entity-id}.yaml`)

```yaml
entity:
  id: entity-id
  name: Display Name
  # any fields provided by user — accessible as {entity.field} in prompts

steps:
  step_id:
    status: pending          # pending | in_progress | done | blocked | skipped | retry_scheduled
    completed_at: ~          # ISO timestamp when done, null otherwise
    completed_by: ~          # "human" or "auto"
    notes: ~                 # optional context or error info
    retry_count: 0           # number of attempts made so far (present only if step has retry config)
    retry_at: ~              # ISO timestamp of next scheduled retry (null unless status is retry_scheduled)
```

## Commands

### `help`

Trigger: "durable-workflow help" / "workflow help" / "how do I use durable-workflow?"

Read and display the linked `README.md` as a formatted summary of all commands and examples.

### `create workflow [name]`

Trigger: "create workflow [name]" / "new workflow" / "define a workflow"

Run the wizard:

1. Ask: **workflow name** (if not given) — lowercase, hyphens only
2. Ask: **entity label** — what is being tracked? (customer / product / partner / etc.)
3. Ask: **description** — one sentence summary
4. Enter step definition loop. For each step:
   - Ask: step name
   - Ask: description (what does this step involve?)
   - Ask: owner (team or person)
   - Ask: depends on which prior steps? (show list of steps defined so far, allow "none" for parallel)
   - Ask: does this step run automatically via a skill? (yes/no)
   - If the user answers with inline skills (e.g. `yes, agentmail`), treat everything after `yes` as the comma-separated skill list
   - If yes: ask for the prompt template immediately after the skills list
   - Ask: should this step retry automatically if it fails? (yes/no)
   - If yes: ask for retry interval (e.g. `6h`, `30m`, `1d`)
   - If yes: ask for max attempts (press enter to skip for unlimited)
   - Ask: should newly unblocked auto steps run automatically? (yes/no) [sets `auto_run_unblocked_steps`]
   - Show the updated ASCII DAG after each step is added
   - Ask: add another step? (yes/no)
5. Show the full DAG and step list for confirmation
6. On confirm: write `~/.claude/workflows/{name}/workflow.yaml`
7. Report the file path and how to start a run

### `start [workflow] for [entity-id], [entity details]`

Trigger: "start [workflow] for [entity]" / "onboard [entity]" / "begin [workflow] for [entity]"

1. Read `~/.claude/workflows/{workflow}/workflow.yaml` — error if not found, suggest `create workflow` first
2. Create `~/.claude/workflows/{workflow}/{entity-id}.yaml` with the entity data provided
   - If the user gave only a display name, derive `entity-id` as a lowercase kebab-case slug unless they explicitly requested a different id.
   - Preserve the human-readable name separately in `entity.name`.
   - Structured payloads may be nested (for example `entity.product.name`); keep the nesting stable and reference those paths consistently in prompts.
3. Set all steps with `depends_on: []` → `status: pending`
4. Set all steps with dependencies → `status: blocked`
5. For steps with `retry` config: initialize `retry_count: 0`, `retry_at: ~`
6. Write the entity YAML
7. If `auto_run_unblocked_steps: true`, immediately run any newly unblocked auto steps in dependency order before returning, starting with all `pending` steps that have `skills` + `prompt` and no unmet dependencies
8. Show file path and initial status summary grouped by: pending (actionable now) | blocked

### `status [workflow] for [entity-id]`

Trigger: "status for [entity]" / "where is [entity] in [workflow]?"

1. Read `~/.claude/workflows/{workflow}/{entity-id}.yaml`
2. Show entity info block
3. Group steps by status: `done` | `in_progress` | `retry_scheduled` | `pending` | `blocked`
4. For `blocked` steps: show which parent steps are not yet done
5. For `retry_scheduled` steps: show `retry_at`, `retry_count`, and `notes`
6. Format the status output as a monospace ASCII table/code block with columns like `Status`, `Step`, and `Details` when presenting step state to the user.
7. Show overall progress: X of Y steps done

### `run [step] in [workflow] for [entity-id]`

Trigger: "run [step] for [entity]" / "execute [step] for [entity]"

Only available when the step has `skills` and `prompt` defined.

1. Read `{entity-id}.yaml` — verify step is `pending` or `retry_scheduled`, error if `blocked` or `done`
2. Read `workflow.yaml` — get step's `skills`, `prompt`, and `retry` config
3. Interpolate `{entity.field}` in the prompt using entity data
4. Set step to `status: in_progress`, write YAML
5. Announce: "Using [skill-a], [skill-b] to run: [step name]"
6. Invoke each skill in `skills` list using the Skill tool
7. Execute the interpolated prompt following those skills
8. **If successful**: set `status: done`, `completed_by: auto`, `completed_at: {now}`; run DAG resolution; report what completed and what unblocked
9. **If not successful and step has `retry` config**:
   - Increment `retry_count`
   - If `max_attempts` is set and `retry_count >= max_attempts`: keep `status: in_progress`, write failure notes, report that max retries reached — do NOT schedule further retries
   - Otherwise: set `status: retry_scheduled`, compute `retry_at = now + interval`, write failure notes and `retry_at` to YAML
   - Use the native `cronjob` tool to create a one-time retry job at `retry_at` for `run {step} in {workflow} for {entity-id}`
   - Create the retry job with `enabled_toolsets` including `cronjob` so the retry can reschedule itself if it fails again
   - Report: "Step failed. Retry scheduled for {retry_at} (attempt {retry_count}/{max_attempts or unlimited})"
10. **If not successful and step has no `retry` config**: keep `status: in_progress`, write failure notes, report what failed and why — do NOT mark done


### Reusable cron retry pattern

For retryable steps that must be represented as a real cron job, use the `cron-retry-rescheduler` skill.

That skill standardizes:
- reading `retry_at` from workflow/entity state
- creating the one-time retry cron job
- verifying the job appears in `cron list`
- ensuring the retry job can schedule the next retry if needed


### `complete [step] in [workflow] for [entity-id]`

Trigger: "mark [step] done for [entity]" / "complete [step] for [entity]"

1. Read `{entity-id}.yaml`
2. Set step: `status: done`, `completed_at: {now}`, `completed_by: human`
3. Preserve any prior failure context in `notes` if the step was previously retry_scheduled or in_progress; manual completion should not erase the troubleshooting trail.
4. Ask for optional notes to record
5. Run DAG resolution (see below)
6. Write updated YAML
7. Report which steps just became unblocked

Pitfall: use the `complete` command only when the user explicitly wants a manual override. If a retryable step hit max attempts, do not auto-convert it to done unless the user has asked for that override.

### `next [workflow] for [entity-id]`

Trigger: "what's next for [entity]?" / "what can we action for [entity]?"

1. Read `{entity-id}.yaml`
2. List all `pending` steps: name, owner, type (auto / manual)
3. List any `in_progress` steps
4. List any `retry_scheduled` steps with their `retry_at` time
5. If all steps done: summarize completion and entity info

### `explain [workflow]`

Trigger: "explain [workflow]" / "what does [workflow] do?" / "show me the [workflow] DAG"

1. Read `workflow.yaml`
2. Group steps: parallel (no deps) → sequential → terminal (depended on by nothing)
3. Draw ASCII dependency tree
4. For each step list: name, description, owner, type (auto / manual), retry config if present

### `list [workflow]`

Trigger: "list [workflow] entities" / "who is in [workflow]?" / "list [workflow] customers"

1. List all `.yaml` files in `~/.claude/workflows/{workflow}/` except `workflow.yaml`
2. For each: show entity name, X of Y steps done, status summary

### `list workflows`

Trigger: "list workflows" / "what workflows exist?" / "show all workflows"

1. List all subdirectories in `~/.claude/workflows/`
2. For each: show workflow name, entity_label, description, number of active entity runs

## DAG resolution (run after every step completion)

```text
for each step where status == "blocked":
    if ALL steps in depends_on have status in [done, skipped]:
        set status = "pending"
write updated entity YAML
```

## Optional auto-advance mode

Some workflows should continue automatically after a step completes. If a workflow enables `auto_run_unblocked_steps: true`, then after DAG resolution Claude should immediately run any newly unblocked steps that:
- are now `pending`
- define `skills` and `prompt`
- are not manual-only

Continue in dependency order until no eligible step remains or a blocked/manual step is encountered. This keeps workflows like onboarding fully hands-off once started, while preserving manual control for workflows that do not opt in.

Pitfall: auto-advance never turns manual steps into auto steps. It only picks up newly unblocked steps that were already declared with `skills` + `prompt`.

## Interval parsing reference

| format | meaning |
|---|---|
| `30m` | 30 minutes |
| `6h` | 6 hours |
| `1d` | 1 day |
| `2h30m` | 2 hours 30 minutes (compound not required — simple forms preferred) |

## Status reference

| status | meaning |
|---|---|
| `pending` | all parents done or skipped — ready to action |
| `in_progress` | being worked or automation running |
| `done` | complete |
| `blocked` | one or more parents not done |
| `skipped` | bypassed — counts as done for dependency resolution |
| `retry_scheduled` | step failed; retry scheduled for `retry_at` |
