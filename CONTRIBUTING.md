# Contributing to Agent Skills Marketplace

Thank you for your interest in contributing! This guide will help you add your skills to the marketplace.

## Quick Contribution Checklist

- [ ] Read this guide completely
- [ ] Use [Skill Writer](./.claude/skills/skill-writer) to create your skill
- [ ] Test your skill thoroughly
- [ ] Follow the directory structure
- [ ] Create all required files
- [ ] Update marketplace.json
- [ ] Submit a pull request

## Getting Started

### Prerequisites

1. **Fork the repository**
   ```bash
   gh repo fork alycd/agent-skills
   # or use GitHub web interface
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/agent-skills.git
   cd agent-skills
   ```

3. **Create a branch**
   ```bash
   git checkout -b add-my-skill
   ```

## Creating Your Skill

### Step 1: Use Skill Writer

Install and use the Skill Writer to ensure quality:

```bash
# Install skill-writer locally
cp -r .claude/skills/skill-writer ~/.claude/skills/

# Ask Claude to help you create the skill
claude
# Then: "Help me create a skill for [your topic]"
```

### Step 2: Required Files

Your skill MUST include these files:

```
.claude/skills/your-skill-name/
├── SKILL.md       # Required
├── README.md      # Required
└── skill.json     # Required
```

#### SKILL.md

Main skill instructions with proper frontmatter:

```yaml
---
name: your-skill-name
description: Brief description with triggers and use cases (max 1024 chars)
---

# Your Skill Name

[Skill content following best practices...]
```

**Requirements:**
- Valid YAML frontmatter
- Name: lowercase, hyphens only, max 64 chars
- Description: specific, includes "Use when...", < 1024 chars
- Clear, actionable instructions
- Concrete examples

#### README.md

User-facing documentation:

```markdown
# Your Skill Name

Brief overview of what the skill does.

## Features
- Feature 1
- Feature 2

## Quick Start
[Simple usage example]

## Installation
[Installation instructions]

## Examples
[Concrete usage examples]
```

#### skill.json

Marketplace metadata:

```json
{
  "id": "your-skill-name",
  "name": "Your Skill Display Name",
  "version": "1.0.0",
  "description": "Same as SKILL.md description",
  "author": "your-github-username",
  "license": "MIT",
  "category": "development|visualization|data|automation|productivity",
  "tags": ["tag1", "tag2", "tag3"],
  "requirements": {
    "tools": ["Write", "Read", "Bash"],
    "external_dependencies": []
  }
}
```

### Step 3: Optional Files

Enhance your skill with:

```
your-skill-name/
├── reference.md       # Detailed API documentation
├── examples.md        # Extended examples
├── scripts/           # Helper utilities
│   └── helper.py
└── templates/         # File templates
    └── template.txt
```

## Testing Your Skill

### Local Testing

1. **Install locally**
   ```bash
   cp -r .claude/skills/your-skill-name ~/.claude/skills/
   ```

2. **Test activation**
   - Start Claude Code
   - Use trigger phrases from your description
   - Verify skill activates correctly

3. **Test functionality**
   - Follow your skill's instructions
   - Try all examples
   - Test edge cases

### Validation

Run these checks:

```bash
# Check YAML frontmatter
head -10 .claude/skills/your-skill-name/SKILL.md

# Verify files exist
ls .claude/skills/your-skill-name/

# Check for common issues
# - Tabs instead of spaces in YAML
# - Missing closing ---
# - Invalid field names
# - Description too long
```

## Updating marketplace.json

Add your skill to the marketplace catalog:

```json
{
  "skills": [
    {
      "id": "your-skill-name",
      "name": "Your Skill Display Name",
      "version": "1.0.0",
      "description": "Same as your SKILL.md description",
      "category": "appropriate-category",
      "tags": ["relevant", "tags", "here"],
      "author": "your-github-username",
      "path": ".claude/skills/your-skill-name",
      "install_url": "https://github.com/alycd/agent-skills/tree/main/.claude/skills/your-skill-name",
      "dependencies": [],
      "requirements": {
        "tools": ["Write", "Read"],
        "external": []
      },
      "features": [
        "Key feature 1",
        "Key feature 2"
      ]
    }
  ]
}
```

**Important:**
- Add to the "skills" array
- Keep existing skills intact
- Update "metadata.skill_count"
- Update "metadata.last_updated"

## Submitting Your Contribution

### Commit Your Changes

```bash
# Add your skill files
git add .claude/skills/your-skill-name/
git add marketplace.json

# Commit with descriptive message
git commit -m "feat: add [skill-name] skill for [purpose]

- Add SKILL.md with [key capability]
- Include README with examples
- Add skill.json metadata
- Update marketplace.json catalog"

# Push to your fork
git push origin add-my-skill
```

### Create Pull Request

1. **Go to GitHub**
   - Navigate to your fork
   - Click "Pull Request"

2. **Fill PR template**
   ```markdown
   ## Skill Information
   - **Name:** your-skill-name
   - **Category:** category
   - **Purpose:** Brief description

   ## Checklist
   - [ ] SKILL.md with valid frontmatter
   - [ ] README.md with examples
   - [ ] skill.json with metadata
   - [ ] marketplace.json updated
   - [ ] Tested locally
   - [ ] No breaking changes

   ## Testing
   Describe how you tested the skill

   ## Additional Notes
   Any special considerations
   ```

3. **Submit and wait for review**

## Review Process

Your PR will be reviewed for:

1. **Quality**
   - Clear, actionable instructions
   - Proper frontmatter
   - Good examples
   - Comprehensive README

2. **Structure**
   - Follows directory conventions
   - Required files present
   - Valid JSON/YAML

3. **Functionality**
   - Skill activates correctly
   - Instructions work as documented
   - No conflicts with existing skills

4. **Documentation**
   - Clear description
   - Proper triggers
   - Example usage

## Skill Quality Guidelines

### Writing Clear Instructions

✅ **Good:**
```markdown
1. Read the input file with Read tool
2. Parse the JSON data
3. Transform using [specific method]
4. Write output with Write tool
```

❌ **Bad:**
```markdown
1. Do stuff with the file
2. Process it somehow
3. Save the result
```

### Effective Descriptions

✅ **Good:**
```yaml
description: Create and manipulate Excel spreadsheets with formulas, charts, and pivot tables. Use when working with .xlsx files, analyzing tabular data, or generating reports.
```

❌ **Bad:**
```yaml
description: Excel helper
description: For spreadsheets and data
```

### Concrete Examples

✅ **Good:**
```markdown
## Example: Create Sales Report

Request: "Create a sales report with monthly totals"

Result:
- Spreadsheet with columns: Month, Sales, Growth%
- Formula calculating growth
- Chart showing trend
```

❌ **Bad:**
```markdown
## Example
You can create reports
```

## Categories

Choose the most appropriate category:

- **development** - Development tools, workflows, testing
- **visualization** - Diagrams, charts, graphics
- **data** - Data processing, analysis, transformation
- **automation** - Workflow automation, scripting
- **productivity** - Document creation, organization
- **security** - Security tools, auditing, analysis

Don't see your category? Propose a new one in your PR!

## Tags

Use descriptive, searchable tags:

**Good tags:**
- File types: `pdf`, `excel`, `json`, `markdown`
- Technologies: `aws`, `docker`, `react`, `python`
- Use cases: `testing`, `debugging`, `visualization`
- Operations: `parsing`, `generation`, `analysis`

**Avoid:**
- Generic: `helper`, `tool`, `utility`
- Redundant: Tags already in category
- Too specific: `my-company-workflow`

## Common Issues

### Skill Doesn't Activate

**Problem:** Claude doesn't use your skill

**Fix:**
- Add more trigger words to description
- Include file types (.pdf, .xlsx)
- Use "Use when..." phrasing
- Test with actual user queries

### Conflicts with Existing Skills

**Problem:** Two skills respond to same query

**Fix:**
- Narrow your skill's scope
- Use more specific description
- Different trigger words
- Consider if skills should merge

### YAML Parse Errors

**Problem:** Frontmatter fails to parse

**Fix:**
- No tabs (use spaces)
- Proper indentation
- Closing `---` required
- No special characters in name

## Getting Help

- **Questions:** Open a [Discussion](https://github.com/alycd/agent-skills/discussions)
- **Issues:** Report [Issues](https://github.com/alycd/agent-skills/issues)
- **Examples:** Study existing skills in the marketplace
- **Guidelines:** Use [Skill Writer](./.claude/skills/skill-writer)

## Code of Conduct

- Be respectful and constructive
- Focus on improving the marketplace
- Help others learn
- Credit original authors
- Follow licensing requirements

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be:
- Listed in skill metadata as author
- Mentioned in release notes
- Credited in CATALOG.md

## Thank You!

Your contribution helps the entire Claude Code community. We appreciate your time and effort in creating quality skills!

---

**Questions?** Open a [Discussion](https://github.com/alycd/agent-skills/discussions)

**Ready to contribute?** Follow the checklist above and submit your PR!
