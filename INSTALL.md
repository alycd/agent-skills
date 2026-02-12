# Installation Guide

This guide will help you install skills from the Agent Skills marketplace.

## Prerequisites

- Claude Code installed and configured
- Git (for git-based installation)
- Basic command-line knowledge

## Installation Methods

### Method 1: Git Clone (Recommended)

This method is best if you want to:
- Install multiple skills
- Get updates easily with `git pull`
- Contribute back to the marketplace

```bash
# 1. Clone the marketplace repository
git clone https://github.com/alycd/agent-skills.git ~/agent-skills

# 2. Copy skills you want to your Claude skills directory
cp -r ~/agent-skills/.claude/skills/draw-io ~/.claude/skills/
cp -r ~/agent-skills/.claude/skills/skill-writer ~/.claude/skills/

# Optional: Install all skills at once
cp -r ~/agent-skills/.claude/skills/* ~/.claude/skills/
```

**Updating skills:**
```bash
cd ~/agent-skills
git pull
cp -r .claude/skills/* ~/.claude/skills/
```

### Method 2: Direct Download (Single Skill)

This method is best if you want to:
- Install just one specific skill
- Avoid cloning the entire repository
- Have a minimal installation

**For Draw.io Diagram Builder:**
```bash
mkdir -p ~/.claude/skills/draw-io
curl -L https://github.com/alycd/agent-skills/archive/main.tar.gz | \
  tar xz --strip=3 -C ~/.claude/skills/draw-io agent-skills-main/.claude/skills/draw-io
```

**For Skill Writer:**
```bash
mkdir -p ~/.claude/skills/skill-writer
curl -L https://github.com/alycd/agent-skills/archive/main.tar.gz | \
  tar xz --strip=3 -C ~/.claude/skills/skill-writer agent-skills-main/.claude/skills/skill-writer
```

### Method 3: Manual Download

1. Go to https://github.com/alycd/agent-skills
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Copy the skill directories from `.claude/skills/` to `~/.claude/skills/`

## Installation Locations

### Personal Skills (Default)
```
~/.claude/skills/
├── draw-io/
├── skill-writer/
└── your-other-skills/
```

Skills installed here are available for:
- All Claude Code sessions
- Your personal workflows
- Any project you work on

### Project-Specific Skills
```
/path/to/your/project/.claude/skills/
├── draw-io/
└── project-specific-skill/
```

Skills installed here are:
- Only available in this project
- Shared with team members (if committed to git)
- Override personal skills with the same name

## Verification

### Check Installation
```bash
# List installed skills
ls ~/.claude/skills/

# Check specific skill
ls ~/.claude/skills/draw-io/SKILL.md
ls ~/.claude/skills/skill-writer/SKILL.md
```

### Test in Claude Code

1. **Start or restart Claude Code**
   ```bash
   claude
   ```

2. **Test skill activation**
   - For draw-io: Say "Create a diagram showing API → Database"
   - For skill-writer: Say "Help me create a new skill"

3. **Verify skill is loaded**
   - Claude should automatically use the skill
   - You'll see skill-specific responses and behavior

## Troubleshooting

### Skill Not Found

**Problem:** Claude doesn't seem to recognize the skill

**Solutions:**
1. Check the installation path:
   ```bash
   ls -la ~/.claude/skills/draw-io/
   ```

2. Verify SKILL.md exists:
   ```bash
   cat ~/.claude/skills/draw-io/SKILL.md | head -20
   ```

3. Restart Claude Code completely

4. Check for YAML errors in frontmatter:
   ```bash
   head -10 ~/.claude/skills/draw-io/SKILL.md
   ```

### Permission Issues

**Problem:** Cannot write to ~/.claude/skills/

**Solution:**
```bash
# Create the directory with proper permissions
mkdir -p ~/.claude/skills
chmod 755 ~/.claude/skills

# Retry installation
cp -r ~/agent-skills/.claude/skills/draw-io ~/.claude/skills/
```

### Skill Conflicts

**Problem:** Multiple skills with the same name

**Solution:**
- Personal skills (`~/.claude/skills/`) override project skills
- Delete or rename conflicting skills
- Check both locations:
  ```bash
  ls ~/.claude/skills/
  ls ./.claude/skills/
  ```

### Outdated Skills

**Problem:** Skill doesn't have latest features

**Solution:**
```bash
# For git installation
cd ~/agent-skills
git pull
cp -r .claude/skills/draw-io ~/.claude/skills/ -f

# For direct download, re-run the curl command
```

## Uninstallation

### Remove Single Skill
```bash
rm -rf ~/.claude/skills/draw-io
# or
rm -rf ~/.claude/skills/skill-writer
```

### Remove All Marketplace Skills
```bash
# Remove specific marketplace skills
rm -rf ~/.claude/skills/draw-io
rm -rf ~/.claude/skills/skill-writer

# Or remove all skills (careful!)
rm -rf ~/.claude/skills/*
```

## Next Steps

1. **Browse the catalog:** See [CATALOG.md](CATALOG.md) for available skills
2. **Read skill documentation:** Each skill has a README.md and SKILL.md
3. **Try examples:** Test the examples in each skill's documentation
4. **Create your own:** Use the Skill Writer to create custom skills

## Advanced Installation

### Symlink for Development

If you're developing skills, you can symlink instead of copying:

```bash
ln -s ~/agent-skills/.claude/skills/draw-io ~/.claude/skills/draw-io
```

This way, changes in the repository immediately reflect in Claude Code.

### Installation Script

Create a script for quick installation:

```bash
#!/bin/bash
# install-skills.sh

REPO_DIR="$HOME/agent-skills"
SKILLS_DIR="$HOME/.claude/skills"

# Clone or update repo
if [ -d "$REPO_DIR" ]; then
  cd "$REPO_DIR" && git pull
else
  git clone https://github.com/alycd/agent-skills.git "$REPO_DIR"
fi

# Install skills
mkdir -p "$SKILLS_DIR"
cp -r "$REPO_DIR/.claude/skills/"* "$SKILLS_DIR/"

echo "✅ Skills installed successfully!"
ls "$SKILLS_DIR"
```

Make it executable:
```bash
chmod +x install-skills.sh
./install-skills.sh
```

## Getting Help

- **Issues:** https://github.com/alycd/agent-skills/issues
- **Discussions:** https://github.com/alycd/agent-skills/discussions
- **Documentation:** See individual skill README files

## Updates

Check for updates regularly:

```bash
cd ~/agent-skills
git pull
cp -r .claude/skills/* ~/.claude/skills/
```

Or watch the repository on GitHub to get notified of new releases.
