# Draw.io Diagram Builder Skill

Create professional Draw.io (diagrams.net) XML diagrams for architecture, network flows, and system designs with proper spacing, icons, grouping, and styling.

## Features

- **AWS/GCP Icon Support** - Built-in hexagonal icons for cloud services
- **Smart Grouping** - Automatic container creation for related components
- **Professional Styling** - Consistent colors, shadows, and spacing
- **Flexible Layouts** - Linear, branching, and grouped diagram flows
- **Validation Built-in** - Ensures proper XML structure and rendering

## Quick Start

1. Request a diagram with flow notation: `A → B → [C, D] → E`
2. The skill will automatically:
   - Parse the flow structure
   - Calculate proper spacing and sizing
   - Choose appropriate icons
   - Generate valid Draw.io XML
   - Save as `.drawio.xml` file

3. Open the result at [app.diagrams.net](https://app.diagrams.net)

## File Structure

```
draw-io/
├── SKILL.md                    # Main instructions and workflow
├── README.md                   # This file
├── templates/
│   └── example-diagram.drawio.xml  # Working example diagram
├── references/
│   └── api-reference.md        # XML syntax, icons, colors
├── assets/                     # Static resources (reserved)
└── scripts/                    # Automation helpers (reserved)
```

## Documentation

- **[SKILL.md](SKILL.md)** - Complete workflow, step-by-step instructions, and best practices
- **[references/api-reference.md](references/api-reference.md)** - Technical reference for XML structure, icon library, color schemes, and validation

## Example Usage

**Simple linear flow:**
```
"Create a diagram: API → Load Balancer → App Server → Database"
```

**With grouping:**
```
"MTA → Gateway → [web1, web2, web3] → Database"
```

**Branching flow:**
```
"Input → Processor → [Storage, Analytics, Notifications]"
```

## Templates

Check the `templates/` directory for working examples you can use as starting points for your own diagrams.

## Contributing

When adding new features or templates:
- Place example diagrams in `templates/`
- Add technical documentation to `references/`
- Update SKILL.md with workflow changes
- Keep this README updated with new capabilities

## License

Part of the Claude Code Skills collection. See LICENSE.txt if applicable.
