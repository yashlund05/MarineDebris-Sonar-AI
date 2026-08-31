# UI_UX_SPEC.md
## MarineDebris-Sonar-AI — UI/UX Specification

**Framework:** React 18 + TypeScript + Tailwind CSS + shadcn/ui  
**Version:** 1.0 — August 2026  

---

## 1. Design Philosophy

The dashboard is a **data-dense, technical tool** — not a consumer app. The visual language prioritises information clarity, sonar image fidelity, and map legibility over decorative design. The aesthetic references sonar and oceanographic software: dark backgrounds (easy on the eye during long survey reviews), high-contrast detection overlays, and clinical typography.

---

## 2. Design Tokens

### 2.1 Color Palette

**Base (Dark Mode — Default)**

| Token | Variable | Hex | Usage |
|---|---|---|---|
| Background Primary | `--color-bg-primary` | `#0A0E14` | Page background, sonar viewer background |
| Background Surface | `--color-bg-surface` | `#131820` | Cards, panels, sidebar |
| Background Elevated | `--color-bg-elevated` | `#1C2433` | Modals, dropdowns, tooltips |
| Border Subtle | `--color-border` | `#2A3547` | Card borders, dividers |
| Text Primary | `--color-text-primary` | `#E8EDF5` | Headings, labels |
| Text Secondary | `--color-text-secondary` | `#8A96A8` | Subtitles, metadata |
| Text Muted | `--color-text-muted` | `#515D6E` | Placeholder, disabled |
| Accent Blue | `--color-accent` | `#3B82F6` | Primary CTA, active nav, links |
| Accent Blue Hover | `--color-accent-hover` | `#2563EB` | Hover state for accent elements |

**Detection Class Colours (Overlay + Map Pins)**

| Class | Token | Hex |
|---|---|---|
| derelict_fishing_gear | `--color-class-gear` | `#F59E0B` (Amber) |
| general_marine_debris | `--color-class-debris` | `#EF4444` (Red) |
| shipwreck | `--color-class-wreck` | `#8B5CF6` (Violet) |
| pipe_or_cylinder | `--color-class-pipe` | `#06B6D4` (Cyan) |
| other_man_made_target | `--color-class-other` | `#84CC16` (Lime) |
| natural_feature (rejected candidate, audit-only — see `PRD.md` §1.1) | `--color-class-natural` | `#6B7280` (Gray) |
| filtered / suppressed (any class, `is_filtered = true`) | `--color-class-filtered` | `#374151` (Dark gray, dashed border) |

`natural_feature` and "filtered" are not primary reportable anomaly classes — they represent the natural-feature/false-positive rejection stage of the detection pipeline. The default `FilterBar` view (`show_filtered = false`) hides both so operators see only artificial-anomaly detections by default; enabling "Show Filtered" reveals them for audit purposes, styled with the dashed/gray treatment above.

**Status Colours**

| Status | Hex |
|---|---|
| Processing / queued | `#F59E0B` |
| Complete | `#10B981` |
| Failed | `#EF4444` |
| Pending | `#6B7280` |

**Light Mode** (optional, toggle-able)  
Light mode uses inverted surface values. Primary background: `#F0F4F8`. Surface: `#FFFFFF`. Text: `#1A202C`. All detection colours remain the same for consistency.

---

### 2.2 Typography

| Role | Font | Size | Weight | Line Height |
|---|---|---|---|---|
| Page Title (H1) | Inter | 24px | 700 | 1.2 |
| Section Header (H2) | Inter | 18px | 600 | 1.3 |
| Card Header (H3) | Inter | 14px | 600 | 1.4 |
| Body / Description | Inter | 14px | 400 | 1.6 |
| Small / Metadata | Inter | 12px | 400 | 1.4 |
| Confidence Badge | JetBrains Mono | 12px | 500 | 1.0 |
| Coordinate Display | JetBrains Mono | 13px | 400 | 1.4 |
| Code / JSON viewer | JetBrains Mono | 12px | 400 | 1.6 |

Fonts loaded from Google Fonts CDN: `Inter:400,500,600,700` and `JetBrains Mono:400,500`.

---

### 2.3 Spacing Scale (Tailwind)

Uses default Tailwind spacing. Key layout values:
- **Sidebar width:** 240px (collapsed: 56px)
- **Top navbar height:** 56px
- **Panel padding:** 16px (p-4)
- **Card gap:** 12px (gap-3)
- **Section margin:** 24px (mb-6)
- **Map height (dashboard):** 40vh minimum, flexible

---

### 2.4 Border Radius

- Buttons, inputs: `rounded-md` (6px)
- Cards, panels: `rounded-lg` (8px)
- Badges/pills: `rounded-full`
- Modal: `rounded-xl` (12px)

---

### 2.5 Shadows

- Cards: `shadow-md` with `shadow-black/30`
- Modals: `shadow-2xl` with `shadow-black/50`
- Dropdowns: `shadow-lg`

---

## 3. Component Inventory

| Component | Location | Description |
|---|---|---|
| `<AppLayout>` | `components/layout/AppLayout.tsx` | Top navbar + sidebar + main content area |
| `<Sidebar>` | `components/layout/Sidebar.tsx` | Collapsible nav with page links and model status badge |
| `<Navbar>` | `components/layout/Navbar.tsx` | Logo, page title, demo mode toggle, dark/light mode |
| `<FileUploader>` | `components/upload/FileUploader.tsx` | Drag-and-drop zone with progress bar; accepts XTF/JSF/PNG/TIFF |
| `<JobStatusBar>` | `components/jobs/JobStatusBar.tsx` | Sticky progress bar with stage label and percentage; connects via WebSocket |
| `<SonarViewer>` | `components/sonar/SonarViewer.tsx` | HTML5 Canvas-based sonar image viewer with pan/zoom |
| `<DetectionOverlay>` | `components/sonar/DetectionOverlay.tsx` | SVG layer over SonarViewer; draws bounding boxes, class labels, confidence |
| `<SonarToggle>` | `components/sonar/SonarToggle.tsx` | Toggle button: Raw ↔ Processed view |
| `<DetectionMap>` | `components/map/DetectionMap.tsx` | Leaflet map with detection pins and survey bounding box |
| `<MapPin>` | `components/map/MapPin.tsx` | Coloured SVG pin per detection class |
| `<DetectionPanel>` | `components/detections/DetectionPanel.tsx` | Right sidebar panel showing detection list with filters |
| `<DetectionCard>` | `components/detections/DetectionCard.tsx` | One card per detection: class badge, confidence, coords, dimensions |
| `<DetectionDetail>` | `components/detections/DetectionDetail.tsx` | Modal/drawer with full detection info + tile image |
| `<ClassBadge>` | `components/ui/ClassBadge.tsx` | Coloured pill badge for detection class |
| `<ConfidenceBadge>` | `components/ui/ConfidenceBadge.tsx` | Monospace confidence % with colour gradient (red→amber→green) |
| `<FilterBar>` | `components/ui/FilterBar.tsx` | Dropdowns/sliders for class, min confidence, show filtered toggle |
| `<ReportDownloader>` | `components/reports/ReportDownloader.tsx` | Button group: Download JSON / CSV / GeoJSON |
| `<ModelInfoBadge>` | `components/ui/ModelInfoBadge.tsx` | Shows active model name, version, device (GPU/CPU) |
| `<ProcessingStatus>` | `components/jobs/ProcessingStatus.tsx` | Pipeline stage indicator with step-by-step visual |
| `<DemoModeBanner>` | `components/ui/DemoModeBanner.tsx` | Yellow banner shown when browsing demo data |
| `<ErrorAlert>` | `components/ui/ErrorAlert.tsx` | Red alert box for job failure or API errors |
| `<EmptyState>` | `components/ui/EmptyState.tsx` | Illustrated empty state with CTA for each page |
| `<MetricsPanel>` | `components/training/MetricsPanel.tsx` | Per-class mAP50/recall/precision table (developer view) |

---

## 4. Page Layout Maps

### 4.1 `/upload` — Upload Page

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR: MarineDebris-Sonar-AI   [Demo Mode] [⚙ Light]  │
├──────────────┬──────────────────────────────────────────┤
│  SIDEBAR     │  MAIN CONTENT                            │
│  • Upload  ← │                                          │
│  • Surveys   │  H1: Upload Sonar File                   │
│  • Map       │  ─────────────────────────────────────   │
│  • Models    │  FileUploader (drag-drop zone)           │
│  ─────────   │   ┌──────────────────────────────────┐   │
│  Model:      │   │  📁 Drop XTF/JSF/PNG here        │   │
│  yolov8m v1  │   │  or click to browse              │   │
│  [GPU ✓]     │   │  Max 2 GB — XTF, JSF, PNG, TIFF  │   │
│              │   └──────────────────────────────────┘   │
│              │  ─────────────────────────────────────   │
│              │  Advanced Options (collapsed accordion)  │
│              │  • Channel: [Starboard ▼]               │
│              │  • Min Confidence: [0.35]               │
│              │  • Run Segmentation: [ ] off            │
│              │  ─────────────────────────────────────   │
│              │  [Upload & Process]                      │
└──────────────┴──────────────────────────────────────────┘
```

---

> Note: `DetectionCard` (320px panel) truncates long canonical class names (e.g. `derelict_fishing_gear` → `derelict_fish…`) with a `title` tooltip showing the full name; `ClassBadge` in wider contexts (map popups, `DetectionDetail`) always shows the full canonical name.

### 4.2 `/surveys/{id}` — Survey Dashboard (primary view)

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAVBAR                                                             │
├─────────┬───────────────────────────────────────┬───────────────────┤
│ SIDEBAR │  SONAR VIEWER PANE (centre-left)       │ DETECTION PANEL  │
│         │                                         │ (right, 320px)  │
│         │  [Raw] [Processed] ← SonarToggle        │                 │
│         │  ┌──────────────────────────────────┐  │ FilterBar:       │
│         │  │                                  │  │ Class [All ▼]    │
│         │  │  < HTML5 Canvas Sonar Image >    │  │ Conf ≥ [0.35]    │
│         │  │  < SVG Detection Overlay >       │  │ [x] Filtered     │
│         │  │                                  │  │ ─────────────── │
│         │  │  Bounding boxes, class labels    │  │ 14 detections   │
│         │  │  coloured by class               │  │                 │
│         │  │                                  │  │ DetectionCard × n│
│         │  └──────────────────────────────────┘  │                 │
│         │  JobStatusBar (if still processing)     │ [D000001]       │
│         │  ─────────────────────────────────────  │ derelict_fish…  │
│         │  MAP PANE (bottom, 40vh)                │ 83% | 3.2×1.1m │
│         │  ┌──────────────────────────────────┐  │ 38.81°N 75.13°W│
│         │  │  Leaflet map                     │  │                 │
│         │  │  Coloured pins per detection     │  │ [D000002]       │
│         │  │  Survey bounding box overlay     │  │ shipwreck       │
│         │  │  Click pin → DetectionDetail     │  │ 91% | 18.4×6.2m│
│         │  └──────────────────────────────────┘  │                 │
│         │  ReportDownloader: [JSON] [CSV] [GeoJSON]│ ...            │
│         │  ModelInfoBadge: yolov8m v1.0.0 | GPU   │               │
└─────────┴───────────────────────────────────────┴─────────────────┘
```

---

### 4.3 `DetectionDetail` Modal

Opens when user clicks a detection card or map pin.

```
┌──────────────────────────────────────────────────┐
│  Detection D000001                          [✕]  │
│  ─────────────────────────────────────────────── │
│  [derelict_fishing_gear]   Final Anomaly Conf: 83%│
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  Sonar tile image with bounding box drawn  │  │
│  │  640 × 640 px crop                        │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Dimensions     3.2 m × 1.1 m                   │
│  Location       38.812345° N, -75.134567° W      │
│                 (or "Geotagging unavailable —    │
│                  no navigation metadata" when    │
│                  geotagging_available = false)   │
│  Ping #         1042   Timestamp: 10:04:11 UTC   │
│  Confidence     Model: 87%   Final Anomaly: 83%  │
│  Filtered       No                               │
│                 (when Yes: shows reason, e.g.    │
│                  "acoustic_shadow_mismatch")     │
│                                                  │
│  Source file    survey_01.xtf                    │
│  Model          sonar_yolov8m_ghostpot_v1 v1.0.0 │
│  Preprocessing  v1.0                             │
│  ─────────────────────────────────────────────── │
│  [View on Map]            [Download tile PNG]    │
└──────────────────────────────────────────────────┘
```

"Model" confidence = raw `confidence` field (Model Confidence, `PRD.md` §1.1); "Final Anomaly" confidence = `confidence_calibrated` field (Final Anomaly Confidence). These labels must be used consistently — do not reintroduce "Raw"/"Calibrated" as the primary labels since "calibrated" alone doesn't communicate that sonar-aware verification also contributed to the number.

All model names, confidence values, and coordinates shown in this and the following mockups are illustrative example data, not real system output.

---

### 4.4 `/surveys` — Survey List Page

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR                                                 │
├─────────┬───────────────────────────────────────────────┤
│ SIDEBAR │  H1: Surveys                  [+ Upload New]  │
│         │  ─────────────────────────────────────────── │
│         │  Search: [              ]                     │
│         │  Filter status: [All ▼]                       │
│         │                                               │
│         │  Table:                                       │
│         │  Filename │ Status │ Detections │ Date │ Actions│
│         │  ─────────────────────────────────────────── │
│         │  survey_01│ ✓ done │ 14         │ Aug31│ [View]│
│         │  survey_02│ ⟳ proc │ —          │ Aug31│ [View]│
│         │  demo_01  │ ✓ done │ 6          │ Demo │ [View]│
└─────────┴───────────────────────────────────────────────┘
```

---

### 4.5 `/models` — Model Registry (Developer View)

All model names and metric values in this mockup are illustrative placeholders; the page renders whatever is actually registered in `model_registry` (`DB_SCHEMA.md` §2.6).

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR                                                 │
├─────────┬───────────────────────────────────────────────┤
│ SIDEBAR │  H1: Model Registry                           │
│         │                                               │
│         │  Active Detection Model                       │
│         │  ┌────────────────────────────────────────┐  │
│         │  │ sonar_yolov8m_ghostpot_v1  v1.0.0       │  │
│         │  │ Architecture: YOLOv8-M                  │  │
│         │  │ Training data: ghost_pot_sss + subpipe  │  │
│         │  │ mAP50: 0.724   mAP50-95: 0.481         │  │
│         │  │ Latency: 42.3 ms (GPU)                  │  │
│         │  └────────────────────────────────────────┘  │
│         │                                               │
│         │  Per-Class Metrics (MetricsPanel)             │
│         │  Class         Prec   Rec   mAP50             │
│         │  fishing_gear  0.81   0.76  0.79              │
│         │  shipwreck     0.88   0.71  0.74              │
│         │  pipe          0.64   0.58  0.61              │
│         │  debris        0.63   0.55  0.59              │
└─────────┴───────────────────────────────────────────────┘
```

`MetricsPanel` abbreviates canonical class names for column width (`fishing_gear` = `derelict_fishing_gear`, `pipe` = `pipe_or_cylinder`, `debris` = `general_marine_debris`); a full-name tooltip is shown on hover, and the underlying data always uses the canonical class names from `PRD.md` §8.

---

## 5. State Tree

### FileUploader States

| State | UI Change |
|---|---|
| **idle** | Drop zone with icon and helper text |
| **dragging** | Drop zone border turns accent blue, background lightens |
| **uploading** | Progress bar with file name and % |
| **success** | Green checkmark, "Processing started" message, redirect to survey page |
| **error** | Red border, error message (file too large / wrong type / server error) |

### JobStatusBar States

| State | UI Change |
|---|---|
| **queued** | Amber pill "Queued" |
| **running** | Animated progress bar, current stage label, % count |
| **complete** | Green bar, "Processing complete — 14 detections found" |
| **failed** | Red bar, error message, [Retry] button |

### SonarViewer States

| State | UI Change |
|---|---|
| **loading** | Skeleton shimmer over canvas |
| **loaded** | Sonar image rendered, panning/zoom enabled |
| **no_image** | EmptyState with "No sonar image available" |
| **error** | ErrorAlert |

### DetectionPanel States

| State | UI Change |
|---|---|
| **loading** | 3 skeleton DetectionCards |
| **empty (no detections)** | EmptyState: "No detections found. Try lowering the confidence threshold." |
| **empty (all filtered)** | EmptyState: "All detections were suppressed. Enable 'Show Filtered' to review them." |
| **populated** | Scrollable list of DetectionCards |

### DetectionMap States

| State | UI Change |
|---|---|
| **loading** | Grey map placeholder |
| **no_nav_data** | Map renders but with banner: "Geotagging unavailable — no navigation metadata in source file" |
| **loaded** | Leaflet map with coloured pins |
| **pin_clicked** | DetectionDetail modal opens |

---

## 6. Responsive Layout

- **≥ 1280px (desktop):** Full 3-column layout (sidebar + sonar viewer + detection panel).
- **1024–1279px:** Detection panel collapses to a bottom drawer triggered by a button.
- **< 1024px (tablet/mobile):** Single column; sonar viewer stacks above map; detection panel is a full-screen drawer.

---

## 7. Accessibility

- All interactive elements have `aria-label` attributes.
- Bounding box overlays include `role="img"` with alt text describing detection class and confidence.
- Colour is never the only indicator of state — always paired with text or icon.
- Keyboard navigation supported for all modals and drawers (focus trap, Esc to close).
- Map pins have tooltip fallback for keyboard users.

---

*End of UI_UX_SPEC.md*
