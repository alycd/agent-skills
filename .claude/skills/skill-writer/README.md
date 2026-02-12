# Skill Writer

A comprehensive guide for creating high-quality Agent Skills for Claude Code with validation, best practices, and testing workflows.

## Overview

Skill Writer helps you create well-structured Agent Skills that follow best practices and validation requirements. Whether you're building your first skill or your tenth, this guide ensures consistent quality and proper structure.

## Features

- ✅ **Guided Workflow** - Step-by-step skill creation process
- ✅ **YAML Validation** - Automatic frontmatter checking
- ✅ **Best Practices** - Industry-standard patterns and conventions
- ✅ **Directory Setup** - Automatic structure creation
- ✅ **Testing Guidance** - Verify skills work correctly
- ✅ **Debug Support** - Troubleshooting common issues

## When to Use This Skill

Use Skill Writer when you want to:
- Create a new Agent Skill from scratch
- Write or update SKILL.md files
- Design proper skill structure and frontmatter
- Troubleshoot skill discovery issues
- Convert existing prompts or workflows into Skills
- Validate existing skills against best practices

## Quick Start

Simply ask Claude to create a skill:

```
Help me create a skill for PDF processing
```

Skill Writer will guide you through:
1. Determining scope and purpose
2. Choosing the right location
3. Creating proper directory structure
4. Writing effective frontmatter
5. Structuring the content
6. Validating the result

## Installation

### Personal Installation
```bash
cp -r /path/to/marketplace/.claude/skills/skill-writer ~/.claude/skills/
```

### Project Installation
```bash
cp -r /path/to/marketplace/.claude/skills/skill-writer ./.claude/skills/
```

## File Structure

```
skill-writer/
├── SKILL.md       # Main skill instructions and workflow
├── README.md      # This file
└── skill.json     # Marketplace metadata
```

## What You'll Learn

### Skill Anatomy
- YAML frontmatter requirements
- Content structure best practices
- File organization patterns
- Progressive disclosure techniques

### Frontmatter Fields
```yaml
---
name: skill-name                    # Required: lowercase, hyphens
description: Brief description...   # Required: max 1024 chars
allowed-tools: Read, Grep, Glob     # Optional: tool restrictions
---
```

### Directory Structure
```
your-skill/
├── SKILL.md              # Required: Main instructions
├── README.md             # Recommended: User documentation
├── reference.md          # Optional: Detailed API docs
├── examples.md           # Optional: Extended examples
├── scripts/              # Optional: Helper utilities
│   └── helper.py
└── templates/            # Optional: File templates
    └── template.txt
```

## Key Concepts

### Effective Descriptions

Your description determines skill discovery. Make it:
- **Specific** - Include trigger words users will say
- **Action-oriented** - What does it do?
- **Context-rich** - When should it be used?

**Good examples:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Bad examples:**
```yaml
description: Helps with documents
description: For data analysis
```

### Tool Restrictions

Limit tool access for security-sensitive or read-only skills:

```yaml
allowed-tools: Read, Grep, Glob  # Read-only skill
```

### Progressive Disclosure

Keep SKILL.md concise by moving details to separate files:
- **SKILL.md** - Overview and quick reference (< 500 words)
- **reference.md** - Detailed API documentation
- **examples.md** - Extended examples and use cases

## Common Patterns

### Simple Single-File Skill
```
skill-name/
└── SKILL.md
```

### Skill with Tools
```
skill-name/
├── SKILL.md
├── README.md
└── scripts/
    └── helper.py
```

### Comprehensive Skill
```
skill-name/
├── SKILL.md
├── README.md
├── reference.md
├── examples.md
├── scripts/
└── templates/
```

## Validation Checklist

Before deploying a skill, verify:

- [ ] Name is lowercase with hyphens only (max 64 chars)
- [ ] Description is specific and under 1024 characters
- [ ] Description includes both "what" and "when"
- [ ] YAML frontmatter is valid (no tabs, proper syntax)
- [ ] Instructions are clear and step-by-step
- [ ] Examples are concrete and realistic
- [ ] Dependencies are documented
- [ ] File paths use forward slashes
- [ ] Skill activates on relevant queries
- [ ] Claude follows instructions correctly

## Troubleshooting

### Skill Doesn't Activate

**Problem:** Claude doesn't recognize the skill

**Solutions:**
1. Make description more specific with trigger words
2. Include file types and operations in description
3. Add "Use when..." clause with user phrases
4. Verify YAML frontmatter is valid
5. Restart Claude Code

### Multiple Skills Conflict

**Problem:** Two skills respond to the same query

**Solutions:**
- Make descriptions more distinct
- Use different trigger words
- Narrow the scope of each skill
- Consider merging related skills

### YAML Errors

**Problem:** Skill fails to load

**Solutions:**
- Check for tabs (use spaces only)
- Verify proper indentation
- Ensure proper `---` markers
- Validate field names and formats

## Best Practices

1. **One Skill, One Purpose** - Don't create mega-skills
2. **Specific Descriptions** - Include trigger words users will say
3. **Clear Instructions** - Write for Claude, not humans
4. **Concrete Examples** - Show real code, not pseudocode
5. **List Dependencies** - Mention required packages in description
6. **Test Thoroughly** - Verify activation and behavior
7. **Version Your Skills** - Document changes
8. **Use Progressive Disclosure** - Keep main file concise

## Examples

### Creating a PDF Skill
```
You: "Help me create a skill for PDF processing"

Claude: "I'll help you create a PDF processing skill. Let me ask a few questions:

1. What specific PDF operations do you need? (extract text, fill forms, merge, split)
2. Do you have existing Python tools or should I recommend some?
3. Is this for personal use or team sharing?

[Interactive workflow continues...]"
```

### Validating a Skill
```
You: "Check if my skill frontmatter is correct"

Claude: [Reads your SKILL.md and validates against requirements]

"I found these issues:
- Name contains uppercase (should be lowercase with hyphens)
- Description is too vague (add specific trigger words)
- Missing 'Use when...' clause

Here are the fixes: [...]"
```

## Advanced Usage

### Read-Only Skills
Perfect for code review or documentation tasks:
```yaml
allowed-tools: Read, Grep, Glob
```

### Script-Based Skills
Include executable tools:
```bash
python scripts/process.py input.csv --output results.json
```

### Multi-File Skills
Organize complex skills with progressive disclosure:
- Quick start in SKILL.md
- Detailed reference in reference.md
- Extended examples in examples.md

## Contributing

Improve Skill Writer by:
- Reporting unclear instructions
- Suggesting new patterns
- Contributing examples
- Updating best practices

## Resources

- **[SKILL.md](./SKILL.md)** - Complete workflow guide
- **[Marketplace](../../README.md)** - Browse other skills
- **[Installation Guide](../../INSTALL.md)** - Setup instructions

## License

MIT License - See repository root for details

## Support

- **Issues:** Report problems on GitHub
- **Discussions:** Ask questions in GitHub Discussions
- **Examples:** Check other marketplace skills for inspiration

---

**Start creating better skills today!**

*Use Skill Writer to ensure your skills follow best practices and work reliably.*
