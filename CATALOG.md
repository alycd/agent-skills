# Agent Skills Catalog

Welcome to the Agent Skills marketplace! This catalog contains professionally crafted skills for Claude Code.

## 📦 Available Skills

### 🎨 Visualization

#### Draw.io Diagram Builder
**Version:** 1.0.0 | **Author:** alycd

Create professional Draw.io (diagrams.net) XML diagrams for architecture, network flows, and system designs.

**Features:**
- ✅ AWS/GCP Icon Support with hex icons
- ✅ Smart Grouping for related components
- ✅ Professional Styling with consistent colors and shadows
- ✅ Flexible Layouts (linear, branching, grouped)
- ✅ Built-in XML Validation

**When to use:**
- Creating architecture diagrams
- Flow charts and network diagrams
- System design visualizations
- Any Draw.io/diagrams.net work

**Quick Example:**
```
Create a diagram: API → Load Balancer → [web1, web2, web3] → Database
```

**[📖 Documentation](./.claude/skills/draw-io/README.md)** | **[⚙️ Install](#installation)**

---

### 🛠️ Development

#### Skill Writer
**Version:** 1.0.0 | **Author:** alycd

Guide users through creating Agent Skills for Claude Code with validation and best practices.

**Features:**
- ✅ Guided skill creation workflow
- ✅ YAML frontmatter validation
- ✅ Best practices enforcement
- ✅ Automatic directory structure setup
- ✅ Testing and debugging guidance
- ✅ Description optimization tips

**When to use:**
- Creating new agent skills
- Writing SKILL.md files
- Validating skill structure
- Learning skill authoring best practices

**Quick Example:**
```
Help me create a skill for PDF processing
```

**[📖 Documentation](./.claude/skills/skill-writer/SKILL.md)** | **[⚙️ Install](#installation)**

---

#### Software Graph Analysis
**Version:** 1.0.0 | **Author:** 0xsarwagya

Build and query Ontoly Software Graphs for deterministic codebase understanding before falling back to source search.

**Features:**
- ✅ Deterministic Software Graph generation
- ✅ Graph-backed architecture summaries
- ✅ Route and request-flow tracing
- ✅ Dependency and impact analysis
- ✅ Diagnostics-aware confidence reporting

**When to use:**
- Architecture summaries and repository onboarding
- Route tracing and request-flow analysis
- Dependency traversal and impact analysis
- Configuration and environment-variable usage review

**Quick Example:**
```
Trace POST /login using the Ontoly Software Graph
```

**[📖 Documentation](./.claude/skills/software-graph-analysis/README.md)** | **[⚙️ Install](#installation)**

---

## Installation

### Quick Install (Single Skill)

To install a specific skill, use one of these methods:

#### Method 1: Git Clone (Recommended)
```bash
# Clone the repository
git clone https://github.com/alycd/agent-skills.git ~/agent-skills

# Copy the skill you want
cp -r ~/agent-skills/.claude/skills/draw-io ~/.claude/skills/

# Or for skill-writer
cp -r ~/agent-skills/.claude/skills/skill-writer ~/.claude/skills/
```

#### Method 2: Direct Download
```bash
# For draw-io
mkdir -p ~/.claude/skills/draw-io
curl -L https://github.com/alycd/agent-skills/archive/main.tar.gz | \
  tar xz --strip=3 -C ~/.claude/skills/draw-io agent-skills-main/.claude/skills/draw-io

# For skill-writer
mkdir -p ~/.claude/skills/skill-writer
curl -L https://github.com/alycd/agent-skills/archive/main.tar.gz | \
  tar xz --strip=3 -C ~/.claude/skills/skill-writer agent-skills-main/.claude/skills/skill-writer
```

### Install All Skills
```bash
# Clone the repository
git clone https://github.com/alycd/agent-skills.git ~/agent-skills

# Copy all skills
cp -r ~/agent-skills/.claude/skills/* ~/.claude/skills/
```

### Verify Installation
After installation, restart Claude Code and verify the skill is available:

```bash
ls ~/.claude/skills/draw-io/SKILL.md
ls ~/.claude/skills/skill-writer/SKILL.md
```

The skills should now be automatically available when you start Claude Code!

## 📊 Browse by Category

### Visualization (1)
- [Draw.io Diagram Builder](#draw-io-diagram-builder)

### Development (2)
- [Skill Writer](#skill-writer)
- [Software Graph Analysis](#software-graph-analysis)

## 🔍 Browse by Tag

| Tag | Skills |
|-----|--------|
| `diagrams` | Draw.io Diagram Builder |
| `architecture` | Draw.io Diagram Builder |
| `aws` | Draw.io Diagram Builder |
| `gcp` | Draw.io Diagram Builder |
| `skill-development` | Skill Writer |
| `authoring` | Skill Writer |
| `documentation` | Skill Writer |
| `meta` | Skill Writer |
| `software-graph` | Software Graph Analysis |
| `architecture` | Software Graph Analysis |
| `dependency-analysis` | Software Graph Analysis |
| `impact-analysis` | Software Graph Analysis |
| `mcp` | Software Graph Analysis |
| `typescript` | Software Graph Analysis |

## 🆕 What's New

**2026-02-12**
- 🎉 Initial marketplace release
- ✨ Added Draw.io Diagram Builder v1.0.0
- ✨ Added Skill Writer v1.0.0

**2026-07-14**
- ✨ Added Software Graph Analysis v1.0.0

## 🤝 Contributing

Want to add your skill to this marketplace?

1. Fork the repository
2. Create your skill in `.claude/skills/your-skill-name/`
3. Follow the [Skill Writer](#skill-writer) guidelines
4. Add your skill metadata to `marketplace.json`
5. Submit a pull request

## 📝 License

See individual skill directories for specific license information.

## 🔗 Links

- **Repository:** https://github.com/alycd/agent-skills
- **Issues:** https://github.com/alycd/agent-skills/issues
- **Discussions:** https://github.com/alycd/agent-skills/discussions

## 📈 Stats

- **Total Skills:** 3
- **Categories:** 2
- **Last Updated:** 2026-02-12
