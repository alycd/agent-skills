# Draw.io XML Technical Reference

## XML Structure Details

### Root Element

```xml
<mxfile host="app.diagrams.net" agent="Claude Code" version="28.1.2">
```

Attributes:
- `host`: Always "app.diagrams.net"
- `agent`: Creator identifier
- `version`: Draw.io version (28.1.2 is current)

### Diagram Element

```xml
<diagram id="unique-id" name="Page-1">
```

Attributes:
- `id`: Unique identifier for the diagram
- `name`: Display name (default "Page-1")

### Graph Model

```xml
<mxGraphModel dx="1554" dy="797" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1" page="1"
              pageScale="1" pageWidth="1400" pageHeight="900"
              background="#ffffff" math="0" shadow="0">
```

Key attributes:
- `dx`, `dy`: Viewport dimensions
- `grid`: Enable grid (1=on, 0=off)
- `gridSize`: Grid spacing in pixels
- `pageWidth`, `pageHeight`: Canvas dimensions
- **`background`**: Canvas background color - **CRITICAL**: Always set to `#ffffff` (white) to ensure white component boxes are visible. Without this, diagrams may render with transparent or gray backgrounds, making white elements invisible

### Cell Structure

All elements are `mxCell` elements:

```xml
<root>
  <mxCell id="0" />                    <!-- Root cell -->
  <mxCell id="1" parent="0" />         <!-- Default layer -->
  <mxCell id="..." parent="1" />       <!-- Your elements -->
</root>
```

## Component Types

### 1. Title Bar

```xml
<mxCell id="title-bar"
        value="Architecture: Title Here"
        style="fillColor=#4DA1F5;strokeColor=none;shadow=1;gradientColor=none;fontSize=14;align=left;spacingLeft=50;fontColor=#ffffff;html=1;"
        parent="1"
        vertex="1">
  <mxGeometry x="100" y="40" width="1200" height="40" as="geometry" />
</mxCell>
```

Style properties:
- `fillColor`: Background color (blue #4DA1F5)
- `strokeColor`: Border (none for title)
- `shadow`: Drop shadow (1=on)
- `fontSize`: Text size
- `align`: Text alignment
- `spacingLeft`: Left padding
- `fontColor`: Text color
- `html`: Enable HTML rendering

### 2. Platform Container

```xml
<mxCell id="platform-container"
        value="&lt;b&gt;Platform Name&lt;/b&gt; Description"
        style="fillColor=#F6F6F6;strokeColor=none;shadow=0;gradientColor=none;fontSize=14;align=left;spacing=10;fontColor=#717171;verticalAlign=top;spacingTop=-4;fontStyle=0;spacingLeft=40;html=1;"
        parent="1"
        vertex="1">
  <mxGeometry x="100" y="120" width="1200" height="700" as="geometry" />
</mxCell>
```

Notes:
- Light gray background (#F6F6F6)
- No border (strokeColor=none)
- No shadow (shadow=0)
- Vertical alignment top
- Negative spacingTop for title positioning

### 3. Component Box (Container)

```xml
<mxCell id="box-id"
        value=""
        style="strokeColor=#dddddd;fillColor=#ffffff;shadow=1;strokeWidth=1;rounded=1;absoluteArcSize=1;arcSize=2;fontSize=10;fontColor=#9E9E9E;align=center;html=1;"
        parent="1"
        vertex="1">
  <mxGeometry x="360" y="250" width="150" height="70" as="geometry" />
</mxCell>
```

Style properties:
- `strokeColor`: Border color
- `fillColor`: Background (white)
- `shadow`: Drop shadow
- `rounded`: Rounded corners
- `arcSize`: Corner radius
- `absoluteArcSize`: Use absolute arc size

### 4. Component Icon Label

```xml
<mxCell id="box-id-label"
        value="&lt;font color=&quot;#000000&quot;&gt;Category&lt;/font&gt;&lt;br&gt;Service Name&lt;hr&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;Description&lt;/font&gt;"
        style="dashed=0;connectable=0;html=1;fillColor=#5184F3;strokeColor=none;shape=mxgraph.gcp2.hexIcon;prIcon=cloud_dataflow;part=1;labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=top;spacingLeft=5;fontColor=#999999;fontSize=12;spacingTop=-8;"
        parent="box-id"
        vertex="1">
  <mxGeometry width="44" height="39" relative="1" as="geometry">
    <mxPoint x="5" y="7" as="offset" />
  </mxGeometry>
</mxCell>
```

Key properties:
- `shape`: Icon shape (mxgraph.gcp2.hexIcon)
- `prIcon`: Icon type (cloud_dataflow, compute_engine, etc.)
- `part`: This is a part of parent (1=yes)
- `labelPosition`: Label relative to icon
- `relative`: Use relative positioning
- `offset`: Position offset from parent

Label structure:
```html
<font color="#000000">Category</font><br>
Service Name
<hr>
<font style="font-size: 11px">Description</font>
```

### 5. Arrow (Edge)

```xml
<mxCell id="edge-id"
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;labelBackgroundColor=none;startFill=1;startSize=4;endArrow=blockThin;endFill=1;endSize=4;jettySize=auto;orthogonalLoop=1;strokeColor=#4284F3;strokeWidth=2;fontSize=12;fontColor=#000000;align=center;dashed=0;"
        parent="1"
        source="box-1"
        target="box-2"
        edge="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

Arrow style properties:
- `edgeStyle`: Routing style (orthogonalEdgeStyle)
- `strokeColor`: Line color (blue #4284F3)
- `strokeWidth`: Line thickness
- `endArrow`: Arrow head type (blockThin)
- `endFill`: Fill arrow head (1=yes)
- `startFill`: Fill start marker
- `dashed`: Dashed line (0=solid)

Routing attributes:
- `source`: Source cell ID
- `target`: Target cell ID
- `edge`: This is an edge (1=yes)

### 6. Arrow with Waypoints

```xml
<mxCell id="edge-id"
        style="..."
        parent="1"
        source="box-1"
        target="box-2"
        edge="1">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="750" y="285" />
      <mxPoint x="750" y="395" />
    </Array>
  </mxGeometry>
</mxCell>
```

Waypoints force arrow routing through specific coordinates.

### 7. Group Container

```xml
<mxCell id="group-id"
        value="&lt;b&gt;Group Title&lt;/b&gt;"
        style="fillColor=#E8F5E9;strokeColor=#81C784;strokeWidth=2;rounded=1;arcSize=5;fontSize=12;align=center;verticalAlign=top;spacingTop=5;fontColor=#2E7D32;html=1;shadow=1;"
        parent="1"
        vertex="1">
  <mxGeometry x="820" y="200" width="240" height="180" as="geometry" />
</mxCell>
```

Group style:
- Colored background (light tint)
- Colored border (darker shade)
- Thicker stroke (2px)
- Title at top (verticalAlign=top)
- Shadow for depth

## Color Schemes

### AWS Colors

- **Primary**: #FF9900 (orange)
- **Secondary**: #232F3E (dark blue)
- **Accent**: #146EB4 (blue)

### GCP Colors

- **Blue**: #4285F4, #5184F3
- **Red**: #EA4335
- **Yellow**: #FBBC04
- **Green**: #34A853

### Group Colors

**Green (Compute/Servers)**:
- Fill: #E8F5E9
- Stroke: #81C784
- Text: #2E7D32

**Orange (Processing)**:
- Fill: #FFF3E0
- Stroke: #FFB74D
- Text: #E65100

**Blue (Storage)**:
- Fill: #E3F2FD
- Stroke: #64B5F6
- Text: #1565C0

**Purple (Services)**:
- Fill: #F3E5F5
- Stroke: #BA68C8
- Text: #4A148C

## Icon Library

### Available prIcon Values

**Compute & Servers**:
- `compute_engine` - Virtual machines
- `app_engine` - Platform services
- `cloud_functions` - Serverless functions
- `kubernetes_engine` - Container orchestration

**Storage**:
- `cloud_storage` - Object storage
- `cloud_sql` - Relational database
- `cloud_bigtable` - NoSQL database
- `persistent_disk` - Block storage

**Networking**:
- `cloud_vpn` - VPN gateway
- `cloud_router` - Network router
- `cloud_load_balancing` - Load balancer
- `cloud_interconnect` - Direct connection

**Data & Analytics**:
- `bigquery` - Data warehouse
- `cloud_dataflow` - Stream/batch processing
- `cloud_dataproc` - Spark/Hadoop
- `cloud_pubsub` - Message queue

**AI & ML**:
- `cloud_ai` - AI services
- `cloud_ml` - Machine learning

**Developer Tools**:
- `cloud_build` - CI/CD
- `cloud_source_repositories` - Source control

## Geometry Calculations

### Box Positioning

For horizontal linear flow:
```
Box N position = start_x + (N * (box_width + spacing))

Example (150px boxes, 50px spacing):
Box 1: x = 140
Box 2: x = 140 + (150 + 50) = 340
Box 3: x = 340 + (150 + 50) = 540
```

### Group Sizing

```
group_width = (num_boxes * box_width) + ((num_boxes - 1) * inner_spacing) + (2 * padding)

Example (3 boxes of 90px, 20px spacing, 20px padding):
width = (3 * 90) + (2 * 20) + (2 * 20) = 270 + 40 + 40 = 350
```

### Canvas Sizing

```
canvas_width = max_x + margin
canvas_height = max_y + margin

Where:
max_x = rightmost_box.x + rightmost_box.width
max_y = bottommost_box.y + bottommost_box.height
margin = 100 (recommended)
```

## HTML Encoding

In XML values, encode these characters:

| Character | Encoded |
|-----------|---------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |
| `"` | `&quot;` |
| `'` | `&apos;` |

Example:
```xml
value="&lt;b&gt;Bold Text&lt;/b&gt;&lt;br&gt;Line Break"
```

Renders as:
```
Bold Text
Line Break
```

## Edge Style Options

### Edge Styles

- `orthogonalEdgeStyle` - Right-angle routing
- `entityRelationEdgeStyle` - ER diagram style
- `elbowEdgeStyle` - Elbow connectors
- `segmentEdgeStyle` - Segmented lines
- `straightEdgeStyle` - Direct line

### Arrow Types

**End arrow (arrow head)**:
- `blockThin` - Thin block arrow
- `block` - Block arrow
- `classic` - Classic arrow
- `diamond` - Diamond marker
- `oval` - Oval marker
- `open` - Open arrow
- `none` - No arrow

**Start arrow** (use `startArrow` property):
Same options as end arrow.

### Line Styles

- `dashed=0` - Solid line
- `dashed=1` - Dashed line
- `strokeWidth=2` - Line thickness

## Performance Tips

1. **Reuse IDs**: Don't duplicate IDs
2. **Minimize waypoints**: Only use when necessary
3. **Group related elements**: Use parent relationships
4. **Consistent spacing**: Use grid alignment
5. **Limit shadows**: Shadows add rendering cost
6. **Optimize canvas size**: Don't make it larger than needed

## Validation

### Required Elements

Every diagram must have:
- [ ] `<mxfile>` root element
- [ ] `<diagram>` element
- [ ] `<mxGraphModel>` element
- [ ] `<root>` element
- [ ] Cell with `id="0"`
- [ ] Cell with `id="1"` and `parent="0"`

### Common Errors

**Invalid XML**:
```xml
<!-- BAD: Unclosed tag -->
<mxCell id="1" parent="0">

<!-- GOOD: Properly closed -->
<mxCell id="1" parent="0" />
```

**Duplicate IDs**:
```xml
<!-- BAD: Same ID used twice -->
<mxCell id="box-1" ... />
<mxCell id="box-1" ... />

<!-- GOOD: Unique IDs -->
<mxCell id="box-1" ... />
<mxCell id="box-2" ... />
```

**Invalid parent reference**:
```xml
<!-- BAD: Parent doesn't exist -->
<mxCell id="child" parent="nonexistent" />

<!-- GOOD: Valid parent -->
<mxCell id="child" parent="1" />
```

**Missing required attributes**:
```xml
<!-- BAD: Edge missing source/target -->
<mxCell id="edge-1" edge="1" />

<!-- GOOD: Complete edge -->
<mxCell id="edge-1" source="box-1" target="box-2" edge="1" />
```

## Advanced Techniques

### Custom Icon Colors

Override icon fill color:
```xml
style="...;fillColor=#FF0000;..."
```

### Multi-line Labels

Use `<br>` for line breaks:
```xml
value="Line 1&lt;br&gt;Line 2&lt;br&gt;Line 3"
```

### Conditional Styling

Add tooltip:
```xml
value="Component Name" tooltip="Additional information"
```

### Layering

Control z-order with parent relationships:
- Background elements: parent="1"
- Foreground elements: parent to background elements

### Connectable Areas

Restrict connection points:
```xml
style="...;connectable=0;..."  <!-- Not connectable -->
```

## Testing Checklist

Before finalizing a diagram:

- [ ] Open in app.diagrams.net without errors
- [ ] All boxes render with proper sizing
- [ ] Text is readable and not clipped
- [ ] Icons display correctly
- [ ] Arrows connect to intended boxes
- [ ] Groups contain correct components
- [ ] Colors match intended scheme
- [ ] No overlapping elements
- [ ] Canvas size is appropriate
- [ ] XML validates (no syntax errors)
- [ ] All IDs are unique
- [ ] Parent references are valid
- [ ] Geometry values are positive
- [ ] Style properties are properly formatted

## Resources

- Draw.io GitHub: https://github.com/jgraph/drawio
- Shape Library: https://github.com/jgraph/drawio/tree/dev/src/main/webapp/shapes
- GCP Icons: https://github.com/jgraph/drawio/blob/dev/src/main/webapp/shapes/mxGCP2.js
- AWS Icons: https://github.com/jgraph/drawio/blob/dev/src/main/webapp/shapes/mxAWS4.js
