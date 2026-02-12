# Claude Code Plugin Marketplace Configuration

This directory contains the marketplace configuration for Claude Code's plugin system.

## Structure

```
.claude-plugin/
└── marketplace.json  # Marketplace configuration (read by Claude Code)
```

## Format

The `marketplace.json` uses Claude Code's plugin marketplace format:

```json
{
  "name": "marketplace-id",
  "owner": { ... },
  "metadata": { ... },
  "plugins": [
    {
      "name": "plugin-name",
      "source": {
        "source": "url",
        "url": "https://github.com/user/repo.git"
      },
      "description": "...",
      "version": "1.0.0",
      "strict": true
    }
  ]
}
```

## Installation Location

This marketplace should be symlinked or cloned to:
```
~/.claude/plugins/marketplaces/<marketplace-name>/
```

For this marketplace:
```bash
ln -s /path/to/agent-skills ~/.claude/plugins/marketplaces/alycd-agent-skills
```

## How It Works

1. Claude Code scans `~/.claude/plugins/marketplaces/` for marketplace directories
2. Each marketplace directory must contain `.claude-plugin/marketplace.json`
3. The marketplace.json lists available plugins with their source URLs
4. Users can browse and install plugins from registered marketplaces

## Difference from Skills

- **Plugin Marketplace**: Lists git repositories that contain plugins/skills
- **Skills Directory**: The actual `.claude/skills/` where skills are installed
- **This Repository**: Acts as both - a plugin marketplace AND a skills repository

Users can either:
- Install via plugin system (if supported by their Claude Code version)
- Manually copy skills from `.claude/skills/` directory (documented in main README.md)
