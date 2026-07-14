# Agent Skills Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Skills: 3](https://img.shields.io/badge/Skills-3-blue.svg)](./CATALOG.md)

A curated marketplace of professional Agent Skills for Claude Code. Install skills to enhance Claude's capabilities with specialized knowledge, workflows, and tools.

## 📚 Available Skills

### 🎨 [Draw.io Diagram Builder](./.claude/skills/draw-io)
Create professional architecture diagrams, flowcharts, and network diagrams with AWS/GCP icons and smart grouping.

**Use cases:** Architecture diagrams, system design, network flows, data pipelines

### 🛠️ [Skill Writer](./.claude/skills/skill-writer)
Guide for creating high-quality Agent Skills with validation, best practices, and testing workflows.

**Use cases:** Creating custom skills, skill authoring, documentation

### 🧭 [Software Graph Analysis](./.claude/skills/software-graph-analysis)
Build and query Ontoly Software Graphs for deterministic codebase understanding.

**Use cases:** Architecture summaries, route tracing, dependency traversal, impact analysis

**[📖 Browse Full Catalog](./CATALOG.md)**

## 📥 Installation

Choose your preferred installation method:

### Method 1: Claude Code (via Plugin Marketplace) (Recommended)
In Claude Code, register the marketplace first:

```bash
/plugin marketplace add alycd/agent-skills
```

Then install the plugin from this marketplace:

```bash
/plugin install agent-skills@alycd-agent-skills
```

### Method 2: Git Clone
```bash
# Install all skills
git clone https://github.com/alycd/agent-skills.git ~/agent-skills
cp -r ~/agent-skills/.claude/skills/* ~/.claude/skills/
```

### Method 3: Single Skill
```bash
# Install just one skill (e.g., draw-io)
mkdir -p ~/.claude/skills/draw-io
curl -L https://github.com/alycd/agent-skills/archive/main.tar.gz | \
  tar xz --strip=3 -C ~/.claude/skills/draw-io agent-skills-main/.claude/skills/draw-io
```

**[📖 Full Installation Guide](./INSTALL.md)**

## 🎯 What Are Agent Skills?

Agent Skills are specialized reference guides that:
- ✅ Extend Claude's capabilities with domain expertise
- ✅ Provide workflows, patterns, and best practices
- ✅ Include templates, tools, and documentation
- ✅ Automatically activate based on user context

## 📁 Repository Structure

```
agent-skills/
├── .claude/
│   └── skills/              # All installable skills
│       ├── draw-io/         # Draw.io diagram builder
│       │   ├── SKILL.md     # Main skill instructions
│       │   ├── README.md    # User documentation
│       │   ├── skill.json   # Marketplace metadata
│       │   ├── templates/   # Example files
│       │   └── references/  # Technical docs
│       ├── skill-writer/    # Skill authoring guide
│       │   ├── SKILL.md
│       │   ├── skill.json
│       │   └── README.md
│       └── software-graph-analysis/
│           ├── SKILL.md
│           ├── README.md
│           └── skill.json
├── .claude-plugin/          # Plugin marketplace config
│   ├── marketplace.json     # Marketplace definition (read by Claude Code)
│   └── README.md            # Marketplace documentation
├── marketplace.json         # Marketplace catalog (for browsing)
├── CATALOG.md              # Browse all skills
├── INSTALL.md              # Installation guide
└── README.md               # This file
```

## 🔍 Finding Skills

**Browse by category:**
- [CATALOG.md](./CATALOG.md) - Full catalog with categories and tags

**Search by use case:**
- Need diagrams? → [draw-io](./.claude/skills/draw-io)
- Creating skills? → [skill-writer](./.claude/skills/skill-writer)
- Understanding a codebase? → [software-graph-analysis](./.claude/skills/software-graph-analysis)

**Filter by tags:**
- `diagrams`, `architecture`, `aws`, `gcp` → Draw.io
- `skill-development`, `authoring`, `documentation` → Skill Writer
- `software-graph`, `dependency-analysis`, `impact-analysis`, `mcp` → Software Graph Analysis

## 🛠️ Using Skills

Once installed, skills work automatically:

1. **Restart Claude Code** (if running)
2. **Ask naturally** - Claude recognizes when to use skills
3. **No manual activation** - Skills trigger based on context

**Examples:**
```bash
# Automatically uses draw-io skill
"Create an architecture diagram: API → LB → App → DB"

# Automatically uses skill-writer skill
"Help me create a skill for PDF processing"
```

## 🤝 Contributing

Want to share your skill with the community?

### Adding a Skill

1. **Fork this repository**
2. **Create your skill** in `.claude/skills/your-skill-name/`
3. **Follow the structure:**
   ```
   your-skill-name/
   ├── SKILL.md       # Required: Main instructions
   ├── README.md      # Required: User documentation
   ├── skill.json     # Required: Marketplace metadata
   └── ...            # Optional: templates, scripts, etc.
   ```
4. **Update marketplace.json** with your skill metadata
5. **Submit a Pull Request**

Use the [Skill Writer](./.claude/skills/skill-writer) to ensure quality!

### Contribution Guidelines

- ✅ Follow existing skill structure and conventions
- ✅ Include comprehensive documentation
- ✅ Add examples and use cases
- ✅ Test your skill thoroughly
- ✅ Use descriptive commit messages

## 📖 Documentation

- **[CATALOG.md](./CATALOG.md)** - Browse all available skills
- **[INSTALL.md](./INSTALL.md)** - Detailed installation instructions
- **[Skill Writer](./.claude/skills/skill-writer/SKILL.md)** - Create your own skills
- **Individual READMEs** - Each skill has detailed documentation

## 🐛 Issues & Support

- **Bug reports:** [Create an issue](https://github.com/alycd/agent-skills/issues)
- **Feature requests:** [Start a discussion](https://github.com/alycd/agent-skills/discussions)
- **Questions:** Check individual skill documentation first

## 📊 Marketplace Stats

- **Total Skills:** 3
- **Categories:** 2 (Visualization, Development)
- **Last Updated:** 2026-07-14
- **License:** MIT

## 🚧 Roadmap

Future enhancements:
- [ ] Web-based skill browser
- [ ] Automatic skill updates
- [ ] Skill dependency management
- [ ] Community voting/ratings
- [ ] CI/CD validation
- [ ] Versioned releases

## 📜 License

This marketplace and individual skills are licensed under the MIT License unless otherwise specified in the skill directory.

See individual skill directories for specific licensing information.

## 🌟 Featured Skills

**Most Popular:**
1. 🎨 [Draw.io Diagram Builder](./.claude/skills/draw-io) - Professional diagram creation
2. 🛠️ [Skill Writer](./.claude/skills/skill-writer) - Create your own skills
3. 🧭 [Software Graph Analysis](./.claude/skills/software-graph-analysis) - Ontoly-backed codebase understanding

**Recently Added:**
- Software Graph Analysis

## 🔗 Links

- **Repository:** https://github.com/alycd/agent-skills
- **Issues:** https://github.com/alycd/agent-skills/issues
- **Discussions:** https://github.com/alycd/agent-skills/discussions
- **Author:** [@alycd](https://github.com/alycd)

---

**Made with ❤️ for the Claude Code community**

*Start building better, faster with specialized Agent Skills!*
