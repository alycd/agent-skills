# Durable Workflow

A skill for defining and running multi-step workflows as dependency graphs (DAGs). Workflows are generic — they can track customers, products, partners, or any entity type. Steps can run in parallel or depend on each other, each step can invoke Claude Code skills automatically or be completed by a human, and steps that fail transiently can be scheduled to retry after a configurable delay.

---

## How it works

1. **Define** a workflow once using the wizard → saved as `workflow.yaml`
2. **Spawn** a run for any entity (customer, product, etc.) → saved as `{entity-id}.yaml`
3. **Run** steps automatically (Claude invokes skills) or **complete** them manually
4. **Retry** — steps with `retry` config schedule themselves to re-run after a delay if they fail
5. **Track** status per entity — Claude knows what's blocked, pending, retrying, and done

```
~/.claude/workflows/
├── onboarding/                  ← workflow for tracking customers
│   ├── workflow.yaml            ← DAG definition (shared)
│   ├── acme-corp.yaml           ← Acme's run state
│   └── globex.yaml              ← Globex's run state
├── product-launch/              ← workflow for tracking products
│   ├── workflow.yaml
│   └── widget-pro.yaml
└── partner-activation/          ← workflow for tracking partners
    ├── workflow.yaml
    └── reseller-a.yaml
```

---

## Quick start

### 1. Create a workflow (wizard)

```
create workflow onboarding
```

Claude will ask you step by step:
- What entity does this track? (e.g. `customer`)
- Add steps one at a time: name, owner, dependencies, optional skills + prompt
- For each auto step: does it retry on failure? If yes: interval (e.g. `6h`) and optional max attempts
- Ask whether newly unblocked auto steps should run automatically (`auto_run_unblocked_steps`)
- See the DAG grow after each step
- Confirm → `workflow.yaml` is written

### 2. Spawn a run for an entity

```
start onboarding for acme-corp, name: Acme Corp, contact: jane@acme.com, plan: enterprise
```

Creates `acme-corp.yaml`. Steps with no dependencies are immediately `pending`; others are `blocked`.

### 3. Check status

```
status onboarding for acme-corp
```

### 4. Run a step automatically

```
run provision_account in onboarding for acme-corp
```

Claude loads the step's skills, interpolates `{entity.field}` values into the prompt, and executes it. If successful, marks done. If it fails and the step has `retry` config, schedules the next attempt automatically.

### 5. Complete a step manually

```
complete send_welcome_email in onboarding for acme-corp
```

### 6. Force a retry now

```
retry check_dns_settings in onboarding for acme-corp
```

Bypasses the scheduled `retry_at` and runs the step immediately.

### 7. See what's next

```
next onboarding for acme-corp
```

---

## All commands

| command | description |
|---|---|
| `create workflow [name]` | Wizard to define a new workflow |
| `start [workflow] for [entity-id], [fields]` | Spawn a new run for an entity |
| `status [workflow] for [entity-id]` | Show step-by-step status for an entity |
| `run [step] in [workflow] for [entity-id]` | Auto-execute a step via its skills |
| `retry [step] in [workflow] for [entity-id]` | Force an immediate retry of a failed/scheduled step |
| `complete [step] in [workflow] for [entity-id]` | Manually mark a step done |
| `next [workflow] for [entity-id]` | List what's actionable right now |
| `explain [workflow]` | Show the DAG and all step descriptions |
| `list [workflow]` | List all entities and their progress |
| `list workflows` | List all workflows that exist |
| `durable-workflow help` | Show this help guide |

---

## Workflow YAML reference

```yaml
name: onboarding
entity_label: customer        # what the tracked entity is called
description: End-to-end onboarding for new customers
auto_run_unblocked_steps: true

steps:
  # Parallel step — no dependencies, starts immediately
  - id: send_welcome_email
    name: Send Welcome Email
    description: Send intro email with login link
    owner: sales
    depends_on: []

  # Auto step with retry — retries every 6h up to 5 times if it fails
  - id: check_dns_settings
    name: Check DNS Settings
    description: Verify DKIM, SPF and DMARC for customer domain
    owner: engineering
    depends_on: [send_welcome_email]
    skills: [dns-checker]
    retry:
      interval: 6h
      max_attempts: 5
    prompt: |
      Use dns-checker to verify that {entity.sending_domain} has correct DKIM, SPF, and DMARC records.
      If all DNS records are valid, complete this step.
      Otherwise report what is missing and do not complete it.

  # Auto step with unlimited retries — keeps retrying every 30m until it succeeds
  - id: provision_account
    name: Provision Account
    description: Create tenant, set plan limits
    owner: engineering
    depends_on: []
    skills: [some-provisioning-skill]
    retry:
      interval: 30m
    prompt: |
      Use some-provisioning-skill to create a tenant for {entity.name}
      with plan {entity.plan} and contact {entity.contact}.
      If provisioning succeeds, complete this step.
      Otherwise report the error and do not complete it.

  # Sequential — waits for one parent
  - id: setup_billing
    name: Configure Billing
    owner: finance
    depends_on: [provision_account]

  # Fan-in — waits for multiple parents
  - id: schedule_kickoff
    name: Schedule Kickoff Call
    owner: cx
    depends_on: [send_welcome_email, assign_csm]

  # Terminal — everything must be done first
  - id: mark_live
    name: Mark Customer Live
    owner: cx
    depends_on: [setup_billing, schedule_kickoff]
```

**The DAG this produces:**

```
send_welcome_email ──► check_dns_settings ──────────────────────────────┐
                                                                         │
assign_csm ─────────────────────────────────► schedule_kickoff ──┐      │
                                                                  ├──► mark_live
provision_account ──► setup_billing ──────────────────────────────┘

[ immediately runnable ]   [ needs parent ]      [ terminal ]
send_welcome_email          check_dns_settings    mark_live
provision_account           setup_billing
assign_csm                  schedule_kickoff
```

### Status output format

When showing workflow status, prefer a monospace ASCII table/code block with columns like `Status`, `Step`, and `Details`.

Example:

```text
Status for Acme (onboarding)

Progress: 1 of 2 steps done

┌─────────────────┬────────────────────┬───────────────────────────────────────────────┐
│ Status          │ Step               │ Details                                       │
├─────────────────┼────────────────────┼───────────────────────────────────────────────┤
│ DONE            │ Send Welcome Email │ Completed manually 2026-05-05T03:30:00Z      │
│ RETRY_SCHEDULED │ Check DNS Settings │ Attempt 2/10 · retry at 2026-05-05T15:30:00Z │
└─────────────────┴────────────────────┴───────────────────────────────────────────────┘
```

### Auto-advance mode

Some workflows should keep moving automatically after a step completes. Set:

```yaml
auto_run_unblocked_steps: true
```

When enabled, any newly unblocked step with `skills` and `prompt` will run automatically after DAG resolution. Manual-only steps still require a human command.

### Retry config reference

| field | required | description |
|---|---|---|
| `interval` | yes | Wait time before next attempt: `30m`, `6h`, `1d` |
| `max_attempts` | no | Maximum attempts before giving up. Omit for unlimited. |

---

## Entity instance file reference

Each entity run lives in `~/.claude/workflows/{workflow}/{entity-id}.yaml`:

```yaml
entity:
  id: acme-corp
  name: Acme Corporation
  contact: jane@acme.com
  plan: enterprise
  sending_domain: mail.acme.com
  # any fields you provided — available as {entity.field} in step prompts

steps:
  send_welcome_email:
    status: done
    completed_at: 2026-05-04T09:00Z
    completed_by: human
    notes: Sent via Mailchimp, opened same day

  provision_account:
    status: done
    completed_at: 2026-05-04T10:30Z
    completed_by: auto
    notes: tenant_id=acme-001, region=us-east-1

  check_dns_settings:
    status: retry_scheduled        # failed — waiting to retry
    completed_at: ~
    completed_by: ~
    notes: "SPF record missing for mail.acme.com"
    retry_count: 1                 # 1 attempt made so far
    retry_at: 2026-05-04T18:00Z   # scheduled for 6h after last failure

  setup_billing:
    status: blocked                # provision_account done but check_dns_settings not yet done
    completed_at: ~
    completed_by: ~
    notes: ~
    retry_count: 0
    retry_at: ~

  schedule_kickoff:
    status: blocked                # assign_csm not done yet
    completed_at: ~
    completed_by: ~
    notes: ~
```

---

## Step status reference

| status | meaning |
|---|---|
| `pending` | all parent steps done — ready to action now |
| `in_progress` | being worked or automation is running |
| `done` | complete |
| `blocked` | one or more parent steps not yet done |
| `skipped` | manually bypassed — counts as done for unblocking children |
| `retry_scheduled` | step failed; retry scheduled for `retry_at` timestamp |

---

## Retry behaviour

When a step with `retry` config fails:

1. `retry_count` is incremented
2. If `retry_count >= max_attempts` (and `max_attempts` is set): no more retries — step stays `in_progress`, failure is recorded
3. Otherwise: status becomes `retry_scheduled`, `retry_at = now + interval` is written to the entity YAML, and a one-time retry job is created via the `cronjob` tool
4. Create the retry job with `enabled_toolsets` including `cronjob`, so the retry can schedule the next retry if needed
5. When the scheduled time arrives, the step runs again automatically

To force an immediate retry at any time (bypassing `retry_at`):
```
retry check_dns_settings in onboarding for acme-corp
```

---

## Using skills in steps

Any step can optionally define `skills` and `prompt`:

```yaml
- id: verify_dns
  name: Verify DNS Records
  owner: engineering
  depends_on: [provision_account]
  skills: [dns-checker, slack-notifier]
  retry:
    interval: 6h
    max_attempts: 10
  prompt: |
    Use dns-checker to verify that {entity.domain} resolves correctly.
    If DNS is correct, use slack-notifier to post a success message to #onboarding.
    If DNS is incorrect, report the failure details and do not complete this step.
```

- `skills` — list of skill names to load before running the prompt
- `prompt` — instructions for Claude; `{entity.field}` is replaced with entity data at runtime
- `retry` — optional; if present, failed runs are rescheduled rather than left as `in_progress`
- Completion is based on the outcome: Claude marks done only if the prompt says to
- Steps without `skills`/`prompt` are manual-only — they must be completed with the `complete` command (retry config has no effect on manual steps)

---

## Multiple workflows

Each workflow lives in its own folder and tracks a different entity type:

```
start onboarding for acme-corp, name: Acme Corp, plan: enterprise
start product-launch for widget-pro, name: Widget Pro, owner: product-team
start partner-activation for reseller-a, name: Reseller A, region: EMEA
```

Check across workflows:

```
list workflows                          → shows all workflow names + entity counts
list onboarding                         → all customers + progress
status product-launch for widget-pro    → widget-pro's step status
```

---

## Tips

- **Entity fields** can be anything you provide at `start` time — they're accessible as `{entity.field}` in all step prompts
- **Skipping a step** (`skipped` status) unblocks its children — use it to bypass steps that don't apply to a specific entity
- **Re-running a failed step** — if a step is `in_progress` after a failed auto-run, fix the issue and run it again or complete it manually
- **Retry steps count as `in_progress` for DAG purposes** — children remain blocked until the step eventually succeeds or is manually completed/skipped
- **Adding steps to an existing workflow** — edit `workflow.yaml` directly; new steps will appear as `blocked` or `pending` on the next status check for each entity (you may need to manually initialize their status in existing entity files)
- **Unlimited retries** — omit `max_attempts` to retry indefinitely; use this for steps that will eventually succeed once external conditions are met (like DNS propagation)
