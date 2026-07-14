---
name: software-graph-analysis
description: Build and query Ontoly Software Graphs for deterministic codebase understanding. Use when the user asks architecture, route tracing, service ownership, dependency traversal, configuration usage, dead-code, or impact-analysis questions before falling back to source search.
---

# Software Graph Analysis

Use Ontoly as the first evidence source for codebase-understanding work. Ontoly builds a deterministic Software Graph containing repository concepts, nodes, relationships, diagnostics, and metadata that can be queried by CLI or MCP.

## Workflow

1. Locate the repository root.
2. Check whether `.ontoly/SoftwareGraph.json` or another supplied Ontoly graph exists.
3. If the graph is missing or stale, run:

   ```bash
   npx ontoly build .
   ```

4. Review graph metadata, diagnostics, graph hash, framework detection, statistics, trust, and coverage.
5. Query Ontoly CLI or MCP capabilities before searching files directly.
6. Answer with graph evidence: node IDs, node kinds, edge names, edge direction, source locations, diagnostics, and confidence.
7. If Ontoly cannot answer, state the missing graph coverage and only then inspect source files as fallback evidence.

## Use Cases

- Architecture summaries and repository onboarding
- Route and request-flow tracing
- Service, module, package, and controller ownership
- Dependency traversal and impact analysis
- Configuration and environment-variable usage
- Dead-code and unreachable-route investigation
- Framework understanding and graph-quality review

## Output Format

```markdown
## Answer
{Direct answer.}

## Graph Evidence
| Kind | Evidence |
|------|----------|
| Node | `{node id}` ({kind}) |
| Edge | `{source} --RELATIONSHIP--> {target}` |
| Location | `{file}:{line}` |
| Diagnostic | `{code}: {message}` |

## Confidence
{High, Medium, or Low} because {specific graph evidence and diagnostics}.

## Gaps
{Missing coverage, ambiguity, or source fallback used.}
```

## Guidelines

- Prefer Ontoly graph queries over grep for architecture, dependency, route, configuration, and impact questions.
- Do not guess confidence; derive it from graph evidence and diagnostics.
- Do not hide low coverage, unresolved imports, missing relationships, or ambiguous nodes.
- Keep answers scoped to the user's question.
- Do not modify the repository unless explicitly asked.

## Example

**Input:**
```
What breaks if UserRepository changes?
```

**Output:**
```markdown
## Answer
AuthService and SessionService directly consume UserRepository. Routes POST /login and POST /logout are in the affected request paths.

## Graph Evidence
| Kind | Evidence |
|------|----------|
| Node | `repository:UserRepository` |
| Edge | `service:AuthService --USES--> repository:UserRepository` |
| Edge | `service:SessionService --USES--> repository:UserRepository` |

## Confidence
High because consumers and route edges are connected in the graph.
```
