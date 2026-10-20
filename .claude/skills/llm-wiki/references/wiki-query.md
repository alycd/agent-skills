# wiki-query — Knowledge Base Query Command

Query Wiki knowledge base and synthesize answers.

**Trigger**: `wiki-query: <question>` or `wiki 查询：<question>`

## Parameter

`$ARGUMENTS` is the query question (natural language), for example:

```
wiki-query: What is RAG?
wiki-query: What key technologies are mentioned in the project?
wiki-query: How do different sources' views on Transformer differ?
```

## Execution Flow

Execute according to **Query Workflow** in SKILL.md:

0. Parse WIKI_ROOT (command-line `@<path>` → `.claude/config/llm-wiki.json` → cwd), all paths based on WIKI_ROOT.
1. If `wiki/index.md` doesn't exist or has no entries, prompt user to run `wiki-ingest` first
2. Read `wiki/index.md`, identify pages most relevant to question (max 10 pages)
3. Use Read tool to read each page
4. Synthesize answer, use `[[PageName]]` wikilink for inline citations; direct quotes no more than 125 characters
5. Append `## Sources` section at end of answer, list all referenced page paths
6. Ask user if they want to save answer as `wiki/syntheses/<slug>.md`
7. Append log to `wiki/log.md`: `## [YYYY-MM-DD] query | <question summary>`

## Output Format Example

```markdown
Based on records in [[RAG]] and [[VectorDB]], Retrieval-Augmented Generation (RAG) is...

## Sources
- wiki/concepts/RAG.md
- wiki/concepts/VectorDB.md
- wiki/sources/paper-rag-survey.md
```
