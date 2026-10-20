# wiki-config — Workspace Path Configuration Command

Configure llm-wiki workspace path so wiki commands can find the correct `raw/`, `wiki/`, `graph/` directories from any location.

**Trigger**: `wiki-config workspace <path>` / `wiki 配置` / `设置 wiki 路径`

---

## Commands

### `wiki-config workspace <path>`

Set workspace path, write to `.claude/config/llm-wiki.json`.

```
wiki-config workspace /Users/me/projects/my-wiki
wiki-config workspace ~/notes/research-wiki
```

**Execution Flow**:

1. Expand path to absolute path (handle `~`)
2. Verify target directory exists; if not, ask user whether to create
3. Read or initialize `.claude/config/llm-wiki.json`, write `workspace` field
4. Output confirmation: `WIKI_ROOT set to /absolute/path`

> See [../config/llm-wiki.example.json](../config/llm-wiki.example.json) for config file format, can copy and edit directly.

---

### `wiki-config show`

Display current WIKI_ROOT source and subdirectory status.

**Example Output**:

```
WIKI_ROOT:   /Users/me/projects/my-wiki   (source: .claude/config/llm-wiki.json)
  raw/       exists
  wiki/      exists
  graph/     not exists (auto-created on first wiki-graph run)
```

If not configured, output:

```
WIKI_ROOT:   /current/working/directory   (source: cwd default)
Tip: Run wiki-config workspace <path> to set a fixed workspace path
```

---

### `wiki-config reset`

Clear the `workspace` field in `.claude/config/llm-wiki.json`, restore to cwd default.

---

## Use Cases

- **Wiki directory not in project root**: Claude Code working directory is a code repo, wiki is in another path
- **Multiple wiki projects**: Use `@<path>` for temporary override, or modify config file to switch
- **CI / Automation**: Specify explicitly via `@<path>`, no need to rely on config file
