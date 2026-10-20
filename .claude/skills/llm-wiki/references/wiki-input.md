# wiki-input — Arbitrary Path File Ingestion Command

Accept files from any local path (or remote OSS path), **copy to `raw/<topic>/` for archiving then ingest**, triggering complete Ingest workflow.

**WIKI_ROOT is strictly determined by `workspace` in `.claude/config/llm-wiki.json`, unrelated to input file path.**

**Trigger**: `wiki-input <path> [--topic <slug>]` / `wiki 输入 <path>`

---

## Command

### `wiki-input <path> [--topic <slug>]`

```
wiki-input ~/Documents/text.pdf --topic oneservice
wiki-input ~/Documents/image.png --topic user-profile
wiki-input ~/Downloads/test1.pptx
wiki-input C:/files/test1.md --topic inbox
wiki-input oss://my-bucket/documents/report.pdf --topic oneservice
wiki-input https://example.com/whitepaper.pdf
```

When `--topic` is not specified, file is archived to `raw/inbox/`.

---

## Execution Flow

### Step 0 — Determine WIKI_ROOT

Read `workspace` field from `.claude/config/llm-wiki.json`, expand `~` to absolute path. If directory doesn't exist, **auto-create complete directory structure at that path** then continue. **Do not infer WIKI_ROOT from input file path, do not fallback to cwd.**

### Step 1 — Path Resolution and Validation

1. Expand path:
   - `~` expands to user home directory
   - Windows paths `C:/...` or `C:\...` used directly
   - Relative paths expanded based on current working directory
2. Verify file exists and is readable; if not, error and terminate
3. Identify file extension, confirm it's a supported type (see supported formats table below)

For remote paths, first download to temp directory, then continue with subsequent steps:

| Path Prefix | Download Method |
|---|---|
| `oss://` | `ossutil cp <path> /tmp/wiki-input-tmp/` |
| `s3://` | `aws s3 cp <path> /tmp/wiki-input-tmp/` |
| `http(s)://` | `curl -L <url> -o /tmp/wiki-input-tmp/<filename>` |

If required CLI tool is unavailable, prompt user to install and terminate.

### Step 1.5 — Determine Topic and Archive to raw/

**Topic Determination Logic:**

1. **Explicit specification**: Command-line `--topic <slug>` passed, use directly
2. **Fallback**: If not specified, put in `raw/inbox/`, and prompt user they can manually move and re-ingest later

**Topic slug rules**: All lowercase, only `a-z`, `0-9`, hyphens, max 32 characters.

Execution steps:
1. If `raw/<topic>/` doesn't exist, auto-create
2. Copy file to `raw/<topic>/<filename>`
3. If same-name file exists, ask user whether to overwrite; if declined, terminate
4. Temp copy of remote file deleted after copy completes

### Step 2 — Trigger Ingest Workflow

Execute complete Ingest flow on `raw/<topic>/<filename>` (dedup check → multimodal extract → Wiki write).

- `source_file` field records `raw/<topic>/<filename>` path
- Original URL / OSS path of remote file recorded in source page's `## Notes` section

---

## Supported File Formats

| Extension | Extraction Method |
|---|---|
| `.md` `.txt` `.json` `.yaml` | Direct Read tool |
| `.pdf` | pdf skill (pdfplumber) |
| `.docx` | docx skill (python-docx) |
| `.pptx` `.ppt` (after conversion) | pptx skill |
| `.xlsx` `.csv` | xlsx skill |
| `.png` `.jpg` `.jpeg` `.webp` | Claude vision |

> `.ppt` (legacy PowerPoint) needs to be converted to `.pptx` first using LibreOffice:
> `libreoffice --headless --convert-to pptx file.ppt`

---

## Remote OSS File Support

### Alibaba Cloud OSS (`oss://`)

**Prerequisites**:
- `ossutil` installed (`ossutil version` executable)
- Access credentials configured (`ossutil config` or environment variables `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET`)
- Read permission on corresponding bucket

### AWS S3 (`s3://`)

**Prerequisites**:
- `aws` CLI installed
- Credentials configured (`aws configure` or environment variables `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)
- IAM permissions include `s3:GetObject`

### Other Remote Protocols

| Protocol | Support Method |
|---|---|
| `http://` / `https://` | curl, no extra dependencies |
| `gs://` | `gsutil cp` (requires Google Cloud SDK) |
| `sftp://` / `scp` | Manual download required, then use local path |

---

## Difference from `wiki-ingest`

| | `wiki-ingest` | `wiki-input` |
|---|---|---|
| File location | Already in `raw/` directory | Any local or remote path |
| File copy | Not needed | Auto-copy to `raw/<topic>/` |
| Topic specification | File path represents topic | `--topic <slug>`, default `inbox` |
| Use case | Manually manage raw/ then ingest | Ingest directly from any location with auto-archive |
