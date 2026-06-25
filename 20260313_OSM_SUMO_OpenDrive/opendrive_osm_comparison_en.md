# OpenDrive vs OpenStreetMap Detailed Comparison

## I. Basic Format

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Header Version | revMinor=4/5 | - |
| Coordinate System | UTM/Geographic | WGS84 |
| Number Format | Decimal/Scientific | Decimal |

**Explanation**:
- OpenDrive uses stricter version control with revMinor distinguishing sub-versions
- OpenDrive supports multiple coordinate systems including local UTM and global geographic coordinates
- OpenStreetMap uses WGS84 latitude/longitude coordinate system

## II. Content Elements

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Lane Width | 3.20-3.75m | 3.75m |
| Lane Marking | Detailed | Basic |
| Speed Information | Available | Available |
| rule Attribute | Available | - |
| surface Element | Available | - |

**Explanation**:
- **Lane Width**: OpenDrive supports independent lane width setting (3.20-3.75m), OSM typically uses default 3.75m
- **Lane Marking**: OpenDrive supports detailed marking types (solid, broken, double lines, etc.), OSM only supports basic markings
- **Speed Information**: Both support, but OpenDrive can set per-lane, OSM typically sets per-road
- **rule Attribute**: OpenDrive has detailed traffic rule attributes, OSM lacks this
- **surface Element**: OpenDrive records pavement material in detail, OSM has limited information

## III. Road Geometry

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Reference line | ✓ | - |
| Curvature (line/arc/clothoid) | ✓ | - |
| Road Length | ✓ | - |
| Elevation | ✓ | - |
| Superelevation | ✓ | - |
| Cross Section Shape | ✓ | - |

**Detailed Explanation**:

1. **Reference Line**
   - **OpenDrive**: Each road has a clear reference line as the basis for geometric description
   - **OSM**: No reference line concept, uses nodes and ways to describe paths

2. **Curvature**
   - **OpenDrive**: Supports three precise geometric types
     - Line: Straight segment
     - Arc: Circular arc
     - Clothoid: Transition curve with linear curvature change for smooth connections
   - **OSM**: Approximates curves with straight segments only, lower precision

3. **Road Length**
   - **OpenDrive**: Calculates and stores each road segment length precisely
   - **OSM**: Length derived from node coordinates, not directly stored

4. **Elevation**
   - **OpenDrive**: Supports 3D elevation information, can describe uphills and downhills
   - **OSM**: Elevation information missing or requires external data sources

5. **Superelevation**
   - **OpenDrive**: Records road cross slope, cant for curves
   - **OSM**: Does not include this information

6. **Cross Section Shape**
   - **OpenDrive**: Detailed description of road cross-section (shoulders, gutters, etc.)
   - **OSM**: Basically not described

## IV. Lane Structure

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Lane ID | ✓ System-assigned unique ID | ✓ Indirectly represented via way and relation |
| Lane Width | ✓ Precise value, variable | △ Estimated via lanes and width tags |
| Lane Type | ✓ Detailed classification (driving, sidewalk, shoulder, etc.) | △ Partial support (lanes:psv, etc.) |
| Lane Connection | ✓ Clear predecessor/successor relationship | ✓ Via turn:lanes tags |
| Speed Limit | ✓ Precise value, lane-level | ✓ maxspeed tag |
| Access Restriction | ✓ Detailed rules (vehicle, pedestrian, etc.) | ✓ access tag |

**Detailed Explanation**:
- **Lane ID**: OpenDrive assigns unique ID to each lane for precise reference; OSM represents indirectly via road way and lane relations
- **Lane Width**: OpenDrive supports variable lane width along the road; OSM typically only has overall road width
- **Lane Type**: OpenDrive supports 10+ lane types; OSM has limited types

## V. Lane Markings

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Solid/Broken Line | ✓ Detailed types (solid, broken, double, etc.) | △ Partial support |
| Color/Width/Lane Change | ✓ Supports color and width, clear lane change rules | ✗ Not supported |
| Pattern/Composite Lines | ✓ Complex pattern support | ✗ Not supported |

**Detailed Explanation**:
- OpenDrive's `<roadMark>` element supports:
  - Types: solid, broken, solid_solid, solid_broken, broken_solid, broken_broken
  - Colors: standard, blue, green, red, white, yellow, orange
  - Width: Precise numeric value
  - Lane change rules: explicit marking
- OSM mainly uses `turn:lanes` tags for indirect representation, lacking detailed geometric and visual information

## VI. Traffic Signs & Signals

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Traffic Signal | ✓ Detailed (position, type, phases) | ✓ highway=traffic_signals |
| Stop Sign | ✓ Supported | ✓ highway=stop |
| Speed Limit Sign | ✓ Precise value and position | ✓ maxspeed + traffic_sign |
| No Entry | ✓ Supported | ✓ access=no |
| Lane-specific Restriction | ✓ Detailed lane-level restrictions | △ Limited support |
| Warning Sign | ✓ Supported | △ Partial support |

**Detailed Explanation**:
- **Traffic Signal**:
  - OpenDrive: `<signal>` element includes complete information like position, type, controller, phases
  - OSM: Simple position marking, no phase and controller information
- **Lane-specific Restriction**:
  - OpenDrive: Can set independent restrictions for each lane
  - OSM: Mainly via `lanes` and `turn:lanes` for indirect representation

## VII. Road Objects

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Stop Line | ✓ Precise geometric position | ✗ Not supported |
| Crosswalk | ✓ Detailed geometry and type | ✓ highway=crossing |
| Road Painting | ✓ Supported | ✗ Not supported |
| Guardrail/Pole | ✓ Supported (guardRail, pole, etc.) | ✗ Not supported |
| Curb/Building | ✓ Supported | ✗ Not supported |
| Parking Space | ✓ Supported | ✓ amenity=parking |
| Barrier/Tunnel/Bridge | ✓ Detailed types | ✓ barrier, tunnel, bridge |

**Detailed Explanation**:
- OpenDrive's `<object>` element supports 30+ road object types
- OSM focuses on functional marking, lacking precise geometric description

## VIII. Intersection Structure

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Connecting Roads | ✓ Clear junction definition | ✓ Connected via ways |
| Turning Relation | ✓ Detailed turning paths | ✓ turn:lanes tags |
| Lane Connection | ✓ Precise lane-level connection | △ Limited support |

**Detailed Explanation**:
- **junction**:
  - OpenDrive: Clearly defines intersection type (default, direct, common), includes all connection relationships
  - OSM: Connected via nodes, no clear intersection structure definition
- **lane connection**:
  - OpenDrive: Clearly defines each lane's connection relationship within `<junction>`
  - OSM: Lacks lane-level connection information

## IX. Road Surface Characteristics

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| Friction Coefficient | ✓ Supported | ✗ Not supported |
| Road Surface Material | ✓ Detailed surface element description | ✓ surface tag |
| Roughness | ✓ Supported | ✗ Not supported |

**Detailed Explanation**:
- OpenDrive's `<surface>` element includes:
  - Friction coefficient
  - Roughness
  - Material type
- OSM only has simple `surface` tag (asphalt, concrete, etc.)

## X. Extension Features

| Element | OpenDrive | OpenStreetMap |
|---------|-----------|---------------|
| userData | ✓ Supports custom extension data | ✗ Not supported |

**Detailed Explanation**:
- OpenDrive's `<userData>` allows adding application-specific custom data
- OSM extends via tags, but lacks structured custom data support

## XI. Application Scenarios

| Application Scenario | OpenDrive | OpenStreetMap |
|---------------------|-----------|---------------|
| Autonomous Driving Simulation | ✓✓ Very suitable | △ Requires extensive supplementation |
| Driving Simulator | ✓✓ Very suitable | ✗ Not suitable |
| Navigation Applications | △ Usable but heavy | ✓✓ Very suitable |
| Route Planning | ✓ Suitable | ✓✓ Very suitable |
| Map Display | △ Usable | ✓✓ Very suitable |
| Traffic Analysis | ✓✓ Very suitable | ✓ Suitable |

---

## Summary Comparison Table

| Category | OpenDrive Advantages | OSM Advantages |
|----------|---------------------|----------------|
| **Precision** | High-precision geometry, suitable for simulation | Global coverage, community maintained |
| **Lane Information** | Detailed lane-level data | Concise and easy to use |
| **3D Information** | Complete 3D support | Lightweight 2D |
| **Traffic Facilities** | Detailed object description | Rich POI data |
| **Extensibility** | Structured extension | Flexible tag system |
| **Data Acquisition** | Requires professional production | Free and open |
| **Update Frequency** | Slower | Real-time updates |

**Conclusion**: OpenDrive is more suitable for high-precision simulation and professional applications, while OpenStreetMap is more suitable for general map services and navigation applications. The two can be used complementarily, combining their respective advantages through conversion tools.

---

**Language / 言語**：[🇨🇳 中文](opendrive_osm_comparison.md) | [🇯🇵 日本語](opendrive_osm_comparison_ja.md) | [🇺🇸 English](opendrive_osm_comparison_en.md)
