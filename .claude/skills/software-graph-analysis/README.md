# Software Graph Analysis

Build and query Ontoly Software Graphs for deterministic codebase understanding.

## Features

- Architecture summaries from graph evidence
- Route and request-flow tracing
- Service, module, package, and controller ownership checks
- Dependency traversal and impact analysis
- Configuration and environment-variable usage review
- Diagnostics-aware confidence reporting

## Quick Start

```bash
npx ontoly build .
npx ontoly mcp
```

Ask questions such as:

```text
Trace POST /login.
What breaks if UserRepository changes?
Which packages depend on AuthModule?
Where is DATABASE_URL used?
```

## Installation

Install this marketplace, then copy or install `.claude/skills/software-graph-analysis` into your Claude Code skills directory.

## Requirements

- Ontoly CLI available through `npx ontoly`, a global install, or a repository-local dev dependency
- A repository that Ontoly can analyze
