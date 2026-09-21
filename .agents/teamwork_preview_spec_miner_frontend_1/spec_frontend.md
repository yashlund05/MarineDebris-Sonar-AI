# Comprehensive Specification: Live Sonar Frontend UI (Requirement R4)

**Document Version:** 1.0  
**Status:** Authoritative Frontend Specification  
**System:** MarineDebris-Sonar-AI (`yashlund05/MarineDebris-Sonar-AI`)  
**Target Milestone:** Live Sonar AI Detection & Tracking Subsystem  

---

## 1. Executive Summary & Specification Scope

This document specifies the complete frontend architecture, component hierarchy, UI/UX behaviors, rendering models, state management, and real-time communication protocols for **Requirement R4: Live Sonar Frontend UI** within the `MarineDebris-Sonar-AI` system.

The implementation builds upon the existing React 18 / TypeScript / Vite / Tailwind CSS / Zustand codebase. It strictly adheres to:
1. **Critical Safety Constraints** (NON-NEGOTIABLE from `ORIGINAL_REQUEST.md`):
   - Zero fabricated data: Unavailable GPS, sonar telemetry, confidence scores, or metrics must explicitly display `NOT_AVAILABLE` or `null`.
   - Frozen dataset & model immutability: Production weights `models/detection/sonar_yolov8_fls_trained.pt` and benchmark datasets remain untouched.
   - Non-breaking architecture: All existing survey, offline inference, dataset explorer, model registry, and enhancement workbench routes remain 100% operational.
2. **Maritime Design Philosophy**:
   - Technical, restrained, professional oceanographic workstation styling.
   - Warm neutral foundations (`#F2EFE7`, `#FFFCF6`, `#E7ECE8`), Dark slate containers (`#0A0E14`, `#131820`, `#0F172A`), Coral/Terracotta primary accent (`#C8523B`, `#AA4332`), and clinical typography (`Inter` and `JetBrains Mono`).
   - No neon cyberpunk or cosmetic dashboard theatre.

---

## 2. Features Discovered

The following features were discovered and documented through exploration of `ORIGINAL_REQUEST.md`, `UI_UX_SPEC.md`, `ARCHITECTURAL_BLUEPRINT.md`, and the existing frontend implementation in `frontend/src/`:

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Routing & Layout | Live Sonar Route (`/live-sonar`) | Primary workstation page for real-time sonar streaming, AI detection, and target tracking. | URL path `/live-sonar`, session query params (`sessionId`) | Rendered full-height viewport with sidebar, navbar, and workspace panes. | If session invalid, shows `SessionNotFoundError` with reconnect action. | `ORIGINAL_REQUEST.md` §R4, `App.tsx` |
| 2 | Navigation | Maritime Nav Integration | Fieldwork section in `Sidebar.tsx` and header context badge in `Navbar.tsx` reflecting active live feed. | Route changes, stream connection state | Active nav link with radar/activity icon, dynamic title "Live Sonar Subsystem". | Shows disconnected badge if backend unreachable. | `components/layout/Sidebar.tsx`, `Navbar.tsx` |
| 3 | Viewport | Multi-Mode Sonar Viewport | Real-time Canvas/WebGL viewport supporting 4 display modes: `RAW`, `ENHANCED`, `AI`, `SPLIT`. | Mode selection, active frame buffer, enhancement profile | Rendered acoustic backscatter with optional radiometric filtering and AI overlays. | Fallback to blank raster with `Stream Degraded` watermark on decoder error. | `ORIGINAL_REQUEST.md` §R4, `SonarViewer.tsx`, `SonarToggle.tsx` |
| 4 | Rendering | Canvas 2D / WebGL Decoupled Render Loop | Decoupled `requestAnimationFrame` render loop consuming an incoming frame buffer independently of WebSocket network jitter. | Decoded image bitmap, target FPS (e.g., 30/60) | High-performance 60 FPS viewport with zero DOM node thrashing. | Drops frame if display queue overflows; increments `display_drops`. | `SonarViewer.tsx`, `package.json` (Three.js/R3F available) |
| 5 | Pan & Zoom | Interactive Pan/Zoom & Fit Controls | Mouse drag pan, scroll wheel zoom (0.25x - 8.0x), reset view, fit-to-viewport, and fullscreen workstation toggle. | Wheel delta, mouse coordinates, keyboard shortcuts (+/-) | Transform matrix applied to canvas / overlay contexts. | Clamps zoom to [0.25, 8.0]; ignores out-of-bounds drags. | `hooks/useSonarViewer.ts`, `SonarViewer.tsx` |
| 6 | Split View | Interactive Comparison Slider / Split | Side-by-side or draggable split-slider comparing Raw vs Enhanced, or Enhanced vs AI-annotated frames. | Split slider position percentage (0–100%), display modes | Dual-buffer clipped canvas rendering with dividing line and grab handle. | Locks slider within [0, 100]; falls back to side-by-side if clipping unsupported. | `BeforeAfterSlider.tsx`, `SideBySideViewer.tsx` |
| 7 | Overlay | Bounding Box Overlay | High-contrast bounding boxes colored by the 5 canonical classes + natural/suppressed classes. | `LiveDetectionEvent[]`, active tracks, class color tokens | SVG or Canvas-rendered bounding boxes with label tags and confidence scores. | Suppressed boxes hidden unless "Show Filtered" toggle active. | `DetectionOverlay.tsx`, `classColors.ts` |
| 8 | Tracking Overlay | Track ID & Confirmation State Badge | Per-target badge displaying `T-{track_id}`, class label, confidence, and confirmation status (Tentative vs Confirmed). | Track state from ByteTrack (`ACTIVE`, `LOST`), frames seen | Solid colored badge for Confirmed; dashed amber outline for Tentative. | Lost tracks grayed out and faded over `lost_patience` frames. | `ORIGINAL_REQUEST.md` §R2, §R4 |
| 9 | Tracking Overlay | Historical Trajectory Trails | Breadcrumb motion trails connecting past centroid coordinates with alpha gradient decay and velocity vector. | Track history `[{x, y, timestamp}]`, velocity vector | Smooth anti-aliased path fading from 1.0 alpha down to 0.05 alpha. | Truncates trail to configured maximum history (e.g. 60 frames) to prevent memory leak. | `ORIGINAL_REQUEST.md` §R4 |
| 10 | Sonar Physics | Acoustic Shadow Indicator | Highlighting acoustic shadow regions down-range behind target centroids to verify physical acoustic occlusion. | Shadow detection status, shadow length/geometry, sonar beam direction | Dashed shadow geometry indicator with "Shadow: Detected" or "Shadow: Unavailable". | Shows `Shadow: NOT_AVAILABLE` if shadow detector unconfigured or missing. | `ORIGINAL_REQUEST.md` §R2, §R4, `UI_UX_SPEC.md` |
| 11 | Target List | Active Targets Sidebar Panel | Real-time list of all active tracks in current field of view, displaying Track ID, class badge, confidence, and status. | Active track dictionary from WebSocket stream | Scrollable, sorted list of `TargetCard` items with quick-select action. | Displays `SearchX` empty state when no active targets detected. | `DetectionPanel.tsx`, `DetectionCard.tsx` |
| 12 | Target Inspection | Detailed Target Inspection Drawer | Comprehensive target modal/drawer showing telemetry, confidence history, trajectory, dimensions, and evidence. | Selected `Track` object, session metadata | Detailed telemetry breakdown; strictly displays `NOT_AVAILABLE` for missing telemetry. | Never displays placeholder or simulated coordinates/telemetry. | `DetectionDetail.tsx`, `ORIGINAL_REQUEST.md` §Acceptance Criteria |
| 13 | Target Inspection | Confidence Sparkline History | Micro-chart inside the inspection panel showing the target's confidence trajectory across observed frames. | Frame confidence array `[{frame, conf}]` | Recharts/SVG mini line chart with threshold guide lines. | Shows flat dashed line if only 1 frame observed. | `DetectionDetail.tsx`, `package.json` (Recharts) |
| 14 | Target Inspection | Multi-Representation Evidence Crops | Keyframe viewer inside inspection drawer displaying raw crop, enhanced crop, and annotated crop side-by-side. | Evidence URLs/base64 crops from backend evidence service | 3-pane image viewer with byte-identical raw verification tag. | Shows `Evidence pending confirmation` until track is confirmed. | `ORIGINAL_REQUEST.md` §R5, `SonarEnhancementWorkbench.tsx` |
| 15 | Live Telemetry | Live Metrics Bar | Comprehensive runtime performance bar displaying Input FPS, Inference FPS, Display FPS, Latency, GPU, Queue, etc. | Metric telemetry frames from backend WebSocket | Monospace telemetry badges with alert color thresholds (green/amber/red). | Renders `BACKPRESSURE WARNING` if input FPS exceeds inference FPS. | `ORIGINAL_REQUEST.md` §R1, §R4 |
| 16 | Source Selection | Connection & Source Panel | Configuration panel selecting stream source: Replay file, RTSP stream, USB camera/device, or ARIS SDK stub. | Source URI, source type, buffer policy, FPS limit | Connection form with validate & connect trigger. | Prevents submission of malformed URIs; sanitizes password tokens. | `ORIGINAL_REQUEST.md` §R1, §R3 |
| 17 | Connection State | Connection State Machine & Failover | Manages stream lifecycle states: `IDLE`, `CONNECTING`, `CONNECTED`, `RECONNECTING`, `CONNECTION_LOST`, `ERROR`. | WebSocket state events, ping/pong timeouts | Distinct status badges; displays `CONNECTION LOST` with last frame timestamp. | Never freezes and pretends; halts inference and informs operator immediately. | `ORIGINAL_REQUEST.md` §R4, `api/ws.ts` |
| 18 | Sonar Telemetry | Live Sonar Header Readout | Displays active sonar model, operating frequency, range, gain, tilt, sound speed, and GNSS lock status. | `SonarMetadata` and `Navigation` packets in frame stream | Monospace telemetry readout in header banner. | Missing telemetry fields render as `NOT_AVAILABLE`; GNSS shows `NO LOCK`. | `ORIGINAL_REQUEST.md` §R1, §R4 |
| 19 | Controls | Stream Operation Controls | Pause/Resume stream, Record session (`● RECORDING`), take Snapshot, and toggle Enhancement/Detection/Tracking. | User click actions | Triggers WebSocket command or REST dispatch; updates UI state. | Disables controls if connection is lost. | `ORIGINAL_REQUEST.md` §R4 |
| 20 | Controls | Replay Control Deck | Controls dedicated to Replay mode: Speed selector (0.25x–4x), frame stepping (+1/-1), pause/play, seek scrubber. | User interaction with scrubber, playback speed buttons | Sends seek/speed commands to backend replay session. | Disabled when running a live hardware/RTSP feed (`LIVE` mode). | `ORIGINAL_REQUEST.md` §R4 |
| 21 | Mode Indicator | Unambiguous LIVE vs REPLAY Tag | Permanent high-contrast badge in viewport signaling whether feed is live hardware or replay file. | Session configuration `source_type` | Red pulsing `● LIVE` badge or Cyan `⟳ REPLAY` badge. | Cannot be overridden or hidden by operator. | `ORIGINAL_REQUEST.md` §R4 |
| 22 | Snapshot | 4-Layer Forensic Snapshot | Captures the active frame across 4 representations: raw raster, enhanced raster, annotated raster, and JSON metadata. | Current frame buffer + tracking metadata | Triggers client-side ZIP packaging or downloads multipart artifact. | Alerts operator if canvas buffer is corrupted or empty. | `ORIGINAL_REQUEST.md` §R4, §R5 |
| 23 | Communication | Real-Time Live Sonar WebSocket Client | Robust WebSocket client subscribing to `/ws/live-sonar/{session_id}` for frames, detections, tracks, and alerts. | Session ID, WebSocket URL | Typed stream of events dispatched to Zustand store. | Automatic exponential backoff reconnection up to 5 attempts. | `api/ws.ts`, `ORIGINAL_REQUEST.md` §R3 |
| 24 | Storage & Cache | Ring Buffer Frame Cache | Bounded client-side memory ring buffer (e.g. 100 frames) allowing instantaneous scrub-back and smooth rendering. | Ingestion of incoming WebSocket preview frames | Retains fixed number of latest frames; evicts oldest via FIFO. | Automatically drops oldest frames when memory cap is reached. | `ARCHITECTURAL_BLUEPRINT.md` §5 |

---

## 3. Edge Cases & Boundary Conditions

| # | Feature | Input / Scenario | Observed / Specified Behavior |
|---|---------|------------------|-------------------------------|
| 1 | Target Inspection | Missing GNSS / Navigation Telemetry | Longitude and Latitude show `NOT_AVAILABLE`. Geolocation status shows `Navigation metadata absent from source stream`. Never fabricates coordinates (0.00, 0.00 or random lat/lon). |
| 2 | Target Inspection | Missing Sonar Physical Telemetry | Range (m), Sound Speed (m/s), and Transducer Frequency (kHz) show `NOT_AVAILABLE`. Dimensions show `NOT_AVAILABLE` instead of guessing 0.0m. |
| 3 | Target Inspection | Missing Acoustic Shadow | Acoustic shadow indicator displays `Shadow support: unavailable`. Never creates a fake shadow polygon. |
| 4 | Stream Connection | Abrupt Server / Network Disconnect | WebSocket triggers `onclose`. State immediately transitions to `CONNECTION LOST`. Shows alert banner: `CONNECTION LOST — Last frame received at HH:MM:SS UTC`. Stream freezes on last valid frame with red warning overlay; does NOT clear viewport or pretend stream is active. |
| 5 | Stream Connection | Connection Retry / Backoff | Retries connection after 1s, 2s, 4s, 8s, 16s (max 5 retries). Status shows `RECONNECTING (Attempt 2/5)...`. If all retries fail, transitions to `DISCONNECTED` with manual `Reconnect` button. |
| 6 | Real-time Rendering | Heavy Backpressure (`input_fps > inference_fps`) | Backend queue fills up; backend sends `buffer_warning`. Metrics bar pulses amber/red: `BACKPRESSURE: PROCESSING FALLING BEHIND`. Dropped frames counter increments. Display continues smoothly at latest received preview. |
| 7 | High-DPI Display | Window moved to 4K / Retina Display (`devicePixelRatio = 2.0` or `3.0`) | Canvas internal buffer scales by `dpr`: `canvas.width = clientWidth * dpr`, CSS styled to `clientWidth`. Renders razor-sharp overlays without pixel blur. |
| 8 | Viewport Mode | Fast View Mode Toggle (RAW ↔ ENHANCED ↔ AI ↔ SPLIT) | State switches instantaneously. Canvas re-renders from current frame's multi-representation cache without re-requesting from server or dropping stream. |
| 9 | Temporal Tracking | Single-Frame Detection Spike (Noise / Glint) | Detection appears for only 1 frame. Tracker classifies it as `TENTATIVE (1/5)`. Bounding box renders with thin dashed amber line and muted label. Never triggers confirmed target alert or persistence. Dissipates when not seen in subsequent frame. |
| 10 | Target Occlusion | Target Temporarily Occluded / Lost | Target missing for 1–3 frames. Tracker enters `LOST` state. Bounding box and trail render at 40% opacity with `T-{id} (Searching...)`. If recovered within `max_lost_frames`, restores `CONFIRMED`. If lost permanently, removed cleanly from active list. |
| 11 | Replay Mode | Replay Scrubbing / Seeking to Frame N | User drags timeline scrubber. WebSocket/REST sends seek request. Frame buffer flushes; new frame at seek timestamp loaded. Tracks reset/reinitialize smoothly for the new temporal epoch. |
| 12 | Window Resizing | Resizing browser or toggling sidebar | ResizeObserver observes viewport container. Canvas redraws immediately maintaining aspect ratio (fit or stretch per configuration). Pan coordinates recentered if out of bounds. |

---

## 4. Live Sonar Route, Layout, and Component Hierarchy

### 4.1 Route Definition & Navigation Placement

The Live Sonar subsystem is accessible via the dedicated route:
```
/live-sonar
```

#### Updates to `frontend/src/App.tsx`:
```tsx
import { LiveSonarPage } from "./pages/LiveSonarPage";

// Route entry inside <Route path="/" element={<AppLayout />}>:
<Route path="live-sonar" element={<LiveSonarPage />} />
```

#### Updates to `frontend/src/components/layout/Sidebar.tsx`:
Add to `workspaceNav` (under the **Fieldwork** category):
```tsx
import { Radio } from "lucide-react";

const workspaceNav = [
  { to: "/", label: "Command center", icon: LayoutDashboard },
  { to: "/live-sonar", label: "Live sonar", icon: Radio }, // New R4 Entry
  { to: "/surveys", label: "Expeditions", icon: MapPinned },
  { to: "/upload", label: "Start an expedition", icon: UploadCloud },
];
```

#### Updates to `frontend/src/components/layout/Navbar.tsx`:
Add page title and subtitle mapping for `/live-sonar`:
```tsx
} else if (location.pathname === "/live-sonar") {
  pageTitle = "Live Sonar Subsystem";
  pageSubtitle = "Real-time acoustic stream detection & tracking";
}
```
And add `<Link to="/live-sonar">Live sonar</Link>` to the mobile navigation drawer.

---

### 4.2 Page Layout Architecture (`LiveSonarPage.tsx`)

The Live Sonar page is designed as a data-dense, technical workstation occupying the full available viewport height (`h-[calc(100vh-5rem)]`):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: Session Info | Source Readout | Sonar Telemetry (Freq, Range) | GNSS | LIVE/REPLAY Tag   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ LIVE METRICS STRIP: INPUT FPS | INFER FPS | DISPLAY FPS | LATENCY | GPU | QUEUE | DROPS | TRACKS  │
├──────────────────────────────────────────────────────────────────────┬───────────────────────────┤
│ MAIN VIEWPORT PANE (Flex-1)                                          │ TARGETS PANE (360px)      │
│ ┌──────────────────────────────────────────────────────────────────┐ │ ┌───────────────────────┐ │
│ │ VIEWPORT TOOLBAR: [RAW] [ENHANCED] [AI] [SPLIT] | Zoom/Pan | Full │ │ │ Active Targets (n)    │ │
│ ├──────────────────────────────────────────────────────────────────┤ │ ├───────────────────────┤ │
│ │                                                                  │ │ │ [Filter: All | Gear..]│ │
│ │                   CANVAS 2D / WEBGL VIEWPORT                     │ │ ├───────────────────────┤ │
│ │                                                                  │ │ │ TargetCard: T-104     │ │
│ │  - Acoustic Backscatter Waterfall Raster                         │ │ │ derelict_fishing_gear │ │
│ │  - High-Contrast Bounding Boxes                                  │ │ │ Conf: 87.4% • CONFIRMED│ │
│ │  - Track Badges (T-104, CONFIRMED)                               │ │ ├───────────────────────┤ │
│ │  - Dynamic Trajectory Trails (Fading Polyline)                   │ │ │ TargetCard: T-105     │ │
│ │  - Down-Range Acoustic Shadow Occlusion Wedges                   │ │ │ shipwreck             │ │
│ │                                                                  │ │ │ Conf: 91.2% • CONFIRMED│ │
│ ├──────────────────────────────────────────────────────────────────┤ │ └───────────────────────┘ │
│ │ STREAM & REPLAY CONTROL DECK                                     │                             │
│ │ [Play/Pause] [● Record] [Snapshot] | Enh [x] Det [x] Track [x]    │                             │
│ │ Replay Bar: [0.5x][1x][2x] [|<] [>|] | Scrubber 00:04:12/00:10:00 │                             │
│ └──────────────────────────────────────────────────────────────────┘ │                             │
└──────────────────────────────────────────────────────────────────────┴───────────────────────────┘
```

---

### 4.3 Component Hierarchy

The component tree for the Live Sonar subsystem is modularly placed in `frontend/src/components/live-sonar/`:

```
frontend/src/
├── pages/
│   └── LiveSonarPage.tsx                   // Master page layout, store provider, lifecycle orchestration
├── components/
│   └── live-sonar/
│       ├── LiveSonarHeader.tsx             // Stream source, sonar model, frequency, GNSS lock, LIVE tag
│       ├── LiveMetricsBar.tsx              // Telemetry strip (FPS, Latency, GPU, Queue, Drops, Active)
│       ├── LiveSonarViewport.tsx           // Viewport container with pan/zoom handlers, resize observer
│       │   ├── LiveCanvasRenderer.tsx      // High-performance Canvas2D/WebGL raster rendering engine
│       │   ├── LiveOverlayRenderer.tsx     // Canvas/SVG overlay: bboxes, track IDs, shadows, trails
│       │   ├── ViewportToolbar.tsx         // Mode selector (RAW/ENH/AI/SPLIT), Zoom/Fit/Reset/Fullscreen
│       │   └── SplitComparisonSlider.tsx   // Integrated draggable split view comparison slider
│       ├── LiveControlDeck.tsx             // Play/Pause, Record, Snapshot, Layer Toggles (Enh, AI, Track)
│       ├── ReplayControlBar.tsx            // Speed selector (0.25x-4x), step frame, timeline seek scrubber
│       ├── ConnectionModal.tsx             // Source configuration dialog (RTSP, File, USB, SDK)
│       ├── targets/
│       │   ├── LiveTargetPanel.tsx         // Right sidebar container, count badge, class filters
│       │   ├── LiveTargetCard.tsx          // Compact card: Track ID, class, confidence, status, age
│       │   └── LiveTargetInspectionDrawer.tsx // Deep inspection modal/drawer: telemetry, trajectory, sparkline
│       └── common/
│           ├── StatusBadge.tsx             // Confirmed vs Tentative vs Lost tracking state badges
│           ├── AcousticShadowTag.tsx       // Shadow support indicator badge
│           └── TelemetryCell.tsx           // Standardized key-value renderer enforcing NOT_AVAILABLE
├── store/
│   └── useLiveSonarStore.ts                // Dedicated high-frequency & session state store
├── api/
│   ├── liveSonarWs.ts                      // WebSocket connection manager for /ws/live-sonar/{session_id}
│   └── liveSonarApi.ts                     // REST API client for session CRUD, lifecycle, evidence
└── hooks/
│   ├── useLiveSonarStream.ts               // Hook encapsulating WS connection, frame queue, liveness
│   └── useLiveCanvasRender.ts              // Hook driving requestAnimationFrame render loop & pan/zoom
└── types/
    └── liveSonar.ts                        // TypeScript interfaces for sessions, frames, tracks, metrics
```

---

## 5. Viewport Modes & Canvas/WebGL Rendering Architecture

### 5.1 Viewport Modes Specification

The viewport supports 4 distinct operational modes selectable via the `ViewportToolbar`:

1. **`RAW` (Unprocessed Acoustic Backscatter)**:
   - Displays the unenhanced raw sonar frame preview as acquired directly from the acoustic sensor.
   - Preserves 100% byte-identical grayscale dynamic range.
   - Useful for verifying raw transducer signal health, gain settings, and detecting water column anomalies.
   - All AI bounding boxes and overlays are hidden by default in this mode.

2. **`ENHANCED` (Radiometrically Filtered & Equalized)**:
   - Displays real-time enhanced imagery processed via the sonar pipeline (CLAHE, 2D-FFT stripe suppression, radiometric slant-range normalization).
   - Supports user-selected acoustic color palettes:
     - `Acoustic Grayscale` (default clinical backscatter)
     - `Amber Fire` (standard sidescan visualization)
     - `Deep Teal / Cyan` (high dynamic range contrast)
     - `Copper Glow`
   - AI overlays remain optional.

3. **`AI` (Annotated Target Intelligence — Primary Mode)**:
   - Displays the enhanced or raw frame with full real-time overlays:
     - Confirmed & tentative target bounding boxes
     - Track identifiers (`T-104`) and class labels
     - Monospace confidence scores
     - Fading trajectory motion trails
     - Down-range acoustic shadow occlusion wedges
     - Selected target focus reticles

4. **`SPLIT` (Side-by-Side / Interactive Split Slider)**:
   - Splits the viewport vertically into two synchronized comparison zones:
     - Left Zone: **Raw Sonar** (labeled `RAW SONAR (UNTOUCHED)`)
     - Right Zone: **Enhanced / AI View** (labeled `ENHANCED + TRACKING`)
   - Features an interactive, draggable vertical divider with circular grab handle (`SplitComparisonSlider`).
   - Supports dragging or clicking to inspect fine signal differences across the divider line.

---

### 5.2 Canvas/WebGL Rendering Architecture

#### The High-Frame-Rate Challenge
Live sonar streams arrive at 15–30 FPS with multiple concurrent tracks, each with trajectory history. Standard React DOM rendering (rendering 100+ `<div>` or `<svg>` elements on every frame) induces garbage collection pauses and drops frame rate to < 15 FPS.

#### Architectural Solution: Decoupled Double-Buffered Canvas Pipeline
1. **Decoupled Worker/Queue**:
   - The WebSocket receives frame messages and pushes preview frames (decoded into `ImageBitmap` via `createImageBitmap(blob)`) into a small ring buffer (size: 3).
   - This prevents WebSocket message processing from blocking UI rendering.
2. **`requestAnimationFrame` Loop**:
   - A dedicated render loop runs at the display's native refresh rate (60 Hz / 120 Hz).
   - On each tick:
     - Checks if a new `ImageBitmap` is ready in the ring buffer.
     - Clears the canvas buffer.
     - Draws the sonar image using GPU-accelerated `ctx.drawImage()`.
     - Draws trajectory paths directly via Canvas 2D path methods (`ctx.beginPath()`, `ctx.stroke()`).
     - Draws bounding boxes, text labels, and shadow wedges.
3. **Coordinate Transformation Pipeline**:
   - Sonar Pixel Coordinates `(x, y)` $\rightarrow$ Canvas Buffer Coordinates $\rightarrow$ Pan/Zoom Screen Coordinates:
     $$x_{\text{screen}} = (x_{\text{canvas}} \cdot \text{zoom}) + \text{pan}_x$$
     $$y_{\text{screen}} = (y_{\text{canvas}} \cdot \text{zoom}) + \text{pan}_y$$
   - Transforms are applied via `ctx.setTransform(zoom, 0, 0, zoom, pan.x, pan.y)` once per frame, allowing effortless pan and zoom without recomputing box coordinates.
4. **Retina / High-DPI Adaptation**:
   - The canvas element tracks `window.devicePixelRatio` (e.g., 2.0).
   - Internal drawing buffer dimension is multiplied by DPR:
     $$\text{canvas.width} = \text{containerWidth} \times \text{DPR}$$
     $$\text{canvas.height} = \text{containerHeight} \times \text{DPR}$$
   - CSS display size is styled to `containerWidth` and `containerHeight`.
   - `ctx.scale(DPR, DPR)` ensures crystal-clear labels and thin 1.5px borders.

---

## 6. Real-Time Overlay Rendering Specification

### 6.1 Bounding Box & Class Color Specification

Bounding boxes must use the canonical taxonomy defined in `PRD.md` §8 and `UI_UX_SPEC.md` §2.1:

| Canonical Class Name | Display Label | Border Color | Fill Color (8% Alpha) | Selected Fill (25% Alpha) |
|---|---|---|---|---|
| `derelict_fishing_gear` | Derelict Fishing Gear | `#D97706` (Amber) | `rgba(217, 119, 6, 0.08)` | `rgba(217, 119, 6, 0.25)` |
| `general_marine_debris` | General Marine Debris | `#DC2626` (Red) | `rgba(220, 38, 38, 0.08)` | `rgba(220, 38, 38, 0.25)` |
| `shipwreck` | Shipwreck | `#7C3AED` (Violet) | `rgba(124, 58, 237, 0.08)` | `rgba(124, 58, 237, 0.25)` |
| `pipe_or_cylinder` | Pipe / Cylinder | `#0891B2` (Cyan) | `rgba(8, 145, 178, 0.08)` | `rgba(8, 145, 178, 0.25)` |
| `other_man_made_target` | Other Man-Made Target | `#16A34A` (Green) | `rgba(22, 163, 74, 0.08)` | `rgba(22, 163, 74, 0.25)` |
| `natural_feature` (Audit) | Natural Feature | `#475569` (Slate) | `rgba(71, 85, 105, 0.08)` | `rgba(71, 85, 105, 0.25)` |

- **Stroke Width**:
  - Unselected target: `1.5px` solid.
  - Selected target: `2.5px` solid with white bracketed corner reticles (length `8px`).
  - Tentative / Unconfirmed target: `1.5px` dashed (`strokeDasharray: [4, 3]`).
  - Suppressed / Filtered target: `1.0px` dark gray dashed.

---

### 6.2 Track ID & Label Tag Rendering

Positioned directly above the top-left corner of the bounding box (or clamped below the top border if box is at $y < 20$):
- **Tag Container**: Dark slate pill (`#0F172A`, 92% opacity, 1px border matching class color, radius `3px`, height `18px`).
- **Tag Content**:
  - `[Track ID]`: Monospace `T-{track_id}` (e.g. `T-104`).
  - `[Class Label]`: Truncated class name.
  - `[Confidence]`: `(87%)` in `JetBrains Mono`.
  - `[State Indicator]`:
    - Confirmed: `● CONFIRMED` (green dot).
    - Tentative: `◌ TENTATIVE (3/5)` (amber hollow circle).
    - Lost: `× LOST` (gray text).

---

### 6.3 Historical Trajectory Trails

For each active track with history length $K \ge 2$:
1. Points array: $P = [(x_0, y_0), (x_1, y_1), \dots, (x_k, y_k)]$ where $(x_k, y_k)$ is current centroid.
2. Rendered as a continuous polyline with an **alpha gradient decay**:
   $$\alpha_i = \left(\frac{i}{K}\right)^{1.5} \times 0.9$$
   - Oldest point ($i=0$): $\alpha \approx 0.05$ (barely visible).
   - Newest point ($i=K$): $\alpha = 0.9$ (vivid class color).
3. **Motion Vector Arrow**:
   - Computed from the velocity vector of the last 5 frames: $(\Delta x, \Delta y)$.
   - An arrowhead line extends from the current centroid pointing in the direction of motion, indicating target drift or ROV relative movement.

---

### 6.4 Acoustic Shadow Occlusion Indicators

Acoustic shadows are essential physical proof of 3D objects resting on or protruding from the seabed:
1. When `acoustic_shadow.detected === true`:
   - A semi-transparent dark polygon (`rgba(15, 23, 42, 0.35)`) is drawn extending from the bottom edge of the highlight box in the direction of acoustic propagation (down-range).
   - A subtle dashed cyan border indicates the shadow extent.
   - Badge overlay: `SHADOW: 2.4m` (or `SHADOW: DETECTED`).
2. When `acoustic_shadow.detected === false` or `status === "NOT_AVAILABLE"`:
   - If acoustic reasoning evaluated shadow as absent: shows small warning tag `SHADOW: MISMATCH`.
   - If shadow module is unavailable: displays `SHADOW: NOT_AVAILABLE` in inspection details; does NOT draw synthetic shadow shapes.

---

## 7. Active Targets List & Target Inspection Panel

### 7.1 Active Targets Sidebar Panel (`LiveTargetPanel.tsx`)

Located on the right side of the workstation (width: `360px`):
1. **Header Bar**:
   - Icon: `<Target className="w-4 h-4 text-accent" />`
   - Title: `ACTIVE TARGETS`
   - Target Count: `[Active: 3 | Confirmed: 2]`
   - Quick Filter Bar: Buttons for `All`, `Confirmed Only`, and class dropdown.
2. **Target Card List**:
   - Scrollable container rendering `LiveTargetCard` components.
   - Each card displays:
     - Header: Track ID badge (`T-104`), Status pill (`CONFIRMED` in emerald, or `TENTATIVE` in amber).
     - Class name with colored class bullet.
     - Confidence badge (e.g. `87.4%`).
     - Observation duration: e.g. `12.4s (37 frames)`.
     - Sonar range: `Range: 14.2m` or `NOT_AVAILABLE`.
     - Selection state: Border turns `#C8523B` with subtle glow when clicked.

---

### 7.2 Detailed Target Inspection Panel (`LiveTargetInspectionDrawer.tsx`)

Opened as a sliding drawer or modal when an operator clicks a `TargetCard` or clicks an active target on the canvas:

#### Strictly Enforced Safety Constraint #3:
**No fake telemetry! Any missing parameter MUST render `NOT_AVAILABLE`.**

#### Data Breakdown Table in Inspection Panel:

| Panel Section | Field | Value Display Rule | Unavailable Fallback |
|---|---|---|---|
| **Identity** | Target Track ID | `T-{track_id}` (e.g., `T-104`) | `NOT_AVAILABLE` |
| | Global Event UUID | Canonical UUID string | `NOT_AVAILABLE` |
| | Classification | Full canonical class name with `ClassBadge` | `NOT_AVAILABLE` |
| | Confirmation State | `CONFIRMED (N/M frames)` or `TENTATIVE` | `NOT_AVAILABLE` |
| **Temporal Evidence** | First Observed | UTC timestamp `YYYY-MM-DD HH:MM:SS.sss` | `NOT_AVAILABLE` |
| | Last Observed | UTC timestamp `YYYY-MM-DD HH:MM:SS.sss` | `NOT_AVAILABLE` |
| | Tracking Duration | Computed elapsed seconds (e.g. `14.8 s`) | `NOT_AVAILABLE` |
| | Frames Observed | Total integer count (e.g. `42 frames`) | `0` |
| | Frames Missing | Count of consecutive dropped detections | `0` |
| **Confidence** | Instantaneous Confidence | Monospace `XX.X%` | `NOT_AVAILABLE` |
| | Calibrated Confidence | Monospace `XX.X%` (temperature scaled) | `NOT_AVAILABLE` |
| | Confidence History | Mini sparkline chart across last 30 frames | Flat dashed gray line |
| **Acoustic Physics** | Acoustic Shadow State | `DETECTED (Length: 2.1m)` or `NOT_DETECTED` | `NOT_AVAILABLE` |
| | Sonar Range | Estimated slant range in meters (e.g. `12.4 m`) | `NOT_AVAILABLE` |
| | Sonar Channel | `Starboard` or `Port` | `NOT_AVAILABLE` |
| | Transducer Frequency | Operating frequency (e.g. `3.0 MHz (ARIS 3000)`) | `NOT_AVAILABLE` |
| **Geolocation** | WGS84 Latitude | Decimal degrees e.g. `38.812345° N` | `NOT_AVAILABLE` |
| | WGS84 Longitude | Decimal degrees e.g. `-75.134567° W` | `NOT_AVAILABLE` |
| | GNSS Quality / HDOP | Satellite lock status (e.g. `DGPS / HDOP 0.8`) | `NOT_AVAILABLE` |
| **Model & Pipeline** | Model Name & Weights | `sonar_yolov8_fls_trained.pt` | `NOT_AVAILABLE` |
| | Model Checkpoint SHA | `e1215c7e...` (verified immutable) | `NOT_AVAILABLE` |
| | Preprocessing Profile | `BALANCED` / `REALTIME` / `QUALITY` | `NOT_AVAILABLE` |
| **Evidence Keyframes** | Multi-crop Viewer | Side-by-side: Raw Crop, Enhanced Crop, AI Crop | `Evidence pending confirmation` |

---

## 8. Live Telemetry & Metrics Bar

### 8.1 Metric Definitions and Formulas

The `LiveMetricsBar` renders as a sticky, high-visibility strip directly above the viewport:

| Metric Token | Label | Description & Source | Alert Threshold (Amber / Red) |
|---|---|---|---|
| `input_fps` | **INPUT FPS** | Acquisition frame rate from source adapter ($1 / \Delta t_{\text{frame}}$). | $< 10.0$ FPS (Amber) / $< 2.0$ FPS (Red) |
| `inference_fps` | **INFERENCE FPS** | Number of YOLOv8 forward passes completed per second. | $< 8.0$ FPS (Amber) |
| `display_fps` | **DISPLAY FPS** | Native Canvas redraw rate measured via `requestAnimationFrame`. | $< 30.0$ FPS (Amber) / $< 15.0$ FPS (Red) |
| `latency_ms` | **LATENCY** | Total round-trip latency from frame capture to WebSocket render. | $> 150 \text{ ms}$ (Amber) / $> 300 \text{ ms}$ (Red) |
| `gpu_device` | **DEVICE / GPU** | Active compute device: e.g. `RTX 4090 (42%)` or `CPU (Fallback)`. | `CPU` fallback (Amber warning pill) |
| `queue_depth` | **QUEUE DEPTH** | Number of unread frames in backend buffer / capacity (e.g. `3 / 30`). | $> 15$ (Amber) / $> 25$ (Red: overflow risk) |
| `dropped_frames` | **DROPPED** | Cumulative frames dropped by backpressure policy. | $> 0$ (Amber) / increasing $> 5/\text{sec}$ (Red) |
| `active_tracks` | **ACTIVE TRACKS** | Current total active object tracks in ByteTrack filter. | N/A (Informational) |
| `confirmed_targets`| **CONFIRMED** | Count of tracks meeting temporal confirmation criteria. | N/A (Informational) |

### 8.2 Backpressure Warning Banner

If `input_fps > inference_fps` for more than 2 consecutive seconds or `queue_depth > 0.8 * max_buffer_size`:
- The metrics bar displays a flashing warning banner:
  ```
  ⚠ BACKPRESSURE DETECTED: Inference rate (10.2 FPS) is slower than acquisition (30.0 FPS).
  Policy: DROP_OLDEST active. 14 frames dropped. Display reflects latest real-time frame.
  ```

---

## 9. Connection Panel, Stream Controls, and Replay Controls

### 9.1 Connection & Source Configuration (`ConnectionModal.tsx`)

Allows the operator to initialize a live sonar session with explicit parameters:
1. **Source Type Dropdown**:
   - `Replay File` (Video `.mp4`, `.mkv`, `.avi`, or Sonar `.xtf`, `.jsf`, PNG folder)
   - `RTSP Stream` (`rtsp://[host]:[port]/[path]`)
   - `USB / Video Device` (`device://0`, `device://1`)
   - `ARIS Sonar Native SDK` (Direct hardware API integration — marked `NOT_CONFIGURED` if hardware unavailable)
2. **URI / Path Input**:
   - Validated against SSRF and shell injection.
   - Credentials are redacted (never displayed in plain text or saved to local storage).
3. **Session Configuration**:
   - Target FPS: `5`, `10`, `15`, `30`
   - Buffer Overflow Policy: `DROP_OLDEST` (default), `DROP_NEWEST`, `FIFO`, `LATEST`
   - Buffer Size: `10` to `100` frames
   - Preprocessing Profile: `REALTIME`, `BALANCED`, `QUALITY`
   - Temporal Confirmation: $N$ frames out of $M$ (e.g., 3 of 5)

---

### 9.2 Connection State Machine & Failure Behavior

The connection status is indicated by a top-right badge:

```
[IDLE] ──(Connect)──> [CONNECTING...] ──(Success)──> [CONNECTED / RUNNING]
                           │                               │
                        (Error)                   (Heartbeat Lost)
                           ▼                               ▼
                        [ERROR] <────────────────── [CONNECTION LOST]
                                                           │
                                                      (Reconnect)
                                                           ▼
                                                  [RECONNECTING (1/5)]
```

#### Disconnect Protocol (Safety Constraint):
- When the stream disconnects or the source drops:
  1. The system **IMMEDIATELY** halts AI inference display updates.
  2. Sets status to `CONNECTION LOST` (bold red badge).
  3. Displays last valid frame with an overlay timestamp:
     `SIGNAL LOST AT 2026-09-19 11:20:45 UTC — Last frame: #10492`
  4. Never freezes silently, loops stale frames, or pretends to continue live tracking.

---

### 9.3 Stream Operation Controls (`LiveControlDeck.tsx`)

Positioned directly below the canvas viewport:
- **`Play / Pause` Button**: Pauses stream consumption without terminating session.
- **`● RECORD` Button**:
  - Toggles recording of raw frames, telemetry, and detections to disk.
  - When active: Pulsing red indicator `● RECORDING (00:03:22)` with elapsed timer.
- **`Snapshot` Button**:
  - Triggers instant 4-representation capture:
    1. Raw frame PNG
    2. Enhanced frame PNG
    3. Annotated detection overlay PNG
    4. Comprehensive metadata JSON (sonar settings, telemetry, detected bboxes, tracks)
  - Packages and triggers direct browser download or persists to session evidence store.
- **Toggles**:
  - `Enhancement`: On / Off (switches between Raw and CLAHE/filtered raster)
  - `AI Detection`: On / Off (shows/hides bounding boxes)
  - `Tracking`: On / Off (shows/hides track IDs and trajectory trails)
- **`LIVE` vs `REPLAY` Indicator**:
  - If source is hardware/RTSP: Displays high-visibility pulsing red badge `● LIVE STREAM`.
  - If source is a recording/file: Displays cyan badge `⟳ REPLAY ARCHIVE`.
  - **Zero ambiguity**: The operator always knows whether they are viewing live operations or historical data.

---

### 9.4 Replay Control Deck (`ReplayControlBar.tsx`)

Rendered only when `source_type === "replay"`:
- **Playback Speed Selector**: `[0.25x] [0.5x] [1.0x] [2.0x] [4.0x]`
- **Step Frame Buttons**:
  - `|< Step -1 Frame`
  - `>| Step +1 Frame`
- **Scrubber Bar**:
  - Interactive slider showing current ping/frame index over total frame count.
  - Timestamp indicator: `00:04:12 / 00:15:30 (Frame 3,780 of 13,950)`.
  - Clicking or dragging scrub slider sends `seek_frame` event to backend session.

---

## 10. State Management & WebSocket Architecture

### 10.1 Zustand Store Architecture (`useLiveSonarStore.ts`)

To guarantee 60 FPS performance, the store separates **high-frequency stream state** (which updates 30 times per second and should NOT trigger full React tree re-renders) from **low-frequency UI state**:

```typescript
export interface LiveSonarState {
  // Low-frequency Session State
  sessionId: string | null;
  sessionStatus: "IDLE" | "CONNECTING" | "CONNECTED" | "DEGRADED" | "STOPPED" | "CONNECTION_LOST" | "ERROR";
  isReplay: boolean;
  sourceType: "replay" | "rtsp" | "usb" | "native";
  sourceUri: string;
  isRecording: boolean;
  recordingDurationSeconds: number;
  
  // Display & Viewport Configuration
  viewportMode: "RAW" | "ENHANCED" | "AI" | "SPLIT";
  colormap: "grayscale" | "amber" | "teal" | "copper";
  enhancementProfile: "REALTIME" | "BALANCED" | "QUALITY";
  splitSliderPosition: number; // 0 to 100%
  zoom: number;
  pan: { x: number; y: number };
  
  // Layer Toggles
  showDetections: boolean;
  showTracks: boolean;
  showTrails: boolean;
  showShadows: boolean;
  showFiltered: boolean;
  selectedClassFilter: string;
  minConfidenceFilter: number;
  
  // Selection
  selectedTrackId: number | null;
  isInspectionOpen: boolean;
  
  // Latest Telemetry & Metrics (Refreshed 2–5 times/sec to avoid render thrashing)
  metrics: LiveSonarMetrics;
  sonarMetadata: LiveSonarMetadata | null;
  navigation: LiveNavigation | null;
  activeTracks: Record<number, LiveTrack>;
  
  // Actions
  setSession: (sessionId: string, sourceType: string, isReplay: boolean) => void;
  setSessionStatus: (status: LiveSonarState["sessionStatus"]) => void;
  setViewportMode: (mode: LiveSonarState["viewportMode"]) => void;
  setSplitSliderPosition: (pos: number) => void;
  setSelectedTrackId: (trackId: number | null) => void;
  setInspectionOpen: (open: boolean) => void;
  updateMetrics: (metrics: LiveSonarMetrics) => void;
  updateTelemetry: (meta: LiveSonarMetadata, nav: LiveNavigation) => void;
  updateTracks: (tracks: LiveTrack[]) => void;
  resetSession: () => void;
}
```

---

### 10.2 WebSocket Protocol Specification

The frontend connects to the FastAPI backend at:
```
ws://{host}/ws/live-sonar/{session_id}
```
(or `wss://` on HTTPS deployments).

#### Protocol Event Catalog:

1. **`frame` Event** (High frequency, 10–30 Hz):
   ```json
   {
     "event": "frame",
     "session_id": "sess_01HXYZ...",
     "frame_id": "frame_10492",
     "sequence_number": 10492,
     "timestamp": 1726744855.123,
     "preview_jpeg_base64": "/9j/4AAQSkZJRg...",
     "format": "jpeg",
     "width": 1024,
     "height": 600,
     "detections": [
       {
         "class_id": 0,
         "class_name": "derelict_fishing_gear",
         "confidence": 0.874,
         "confidence_calibrated": 0.841,
         "bbox": [245, 180, 85, 62],
         "track_id": 104,
         "is_confirmed": true
       }
     ],
     "tracks": [
       {
         "track_id": 104,
         "class_name": "derelict_fishing_gear",
         "confidence": 0.874,
         "bbox": [245, 180, 85, 62],
         "status": "ACTIVE",
         "frames_seen": 42,
         "first_seen_timestamp": 1726744840.0,
         "last_seen_timestamp": 1726744855.123,
         "trajectory": [[210, 160], [225, 170], [245, 180]],
         "velocity": [1.3, 0.6],
         "acoustic_shadow": {
           "detected": true,
           "length_m": 2.4,
           "confidence": 0.82
         }
       }
     ],
     "sonar_metadata": {
       "frequency_hz": 3000000,
       "range_m": 15.0,
       "gain": 72,
       "sound_speed_mps": 1500.0
     },
     "navigation": {
       "latitude": 38.812345,
       "longitude": -75.134567,
       "heading": 142.5,
       "depth_m": 18.2,
       "gnss_status": "LOCKED"
     }
   }
   ```

2. **`metrics` Event** (Medium frequency, 2–5 Hz):
   ```json
   {
     "event": "metrics",
     "session_id": "sess_01HXYZ...",
     "input_fps": 29.8,
     "inference_fps": 10.2,
     "latency_ms": 41.5,
     "gpu_name": "NVIDIA RTX 4090",
     "gpu_utilization_pct": 38.0,
     "queue_depth": 3,
     "max_queue_depth": 30,
     "dropped_frames": 0,
     "active_tracks_count": 3,
     "confirmed_tracks_count": 2
   }
   ```

3. **Lifecycle & Alert Events**:
   - `session_started`: Confirms acquisition pipeline initialized.
   - `session_stopped`: Dispatched when operator halts session.
   - `connection_lost`: Source stream dropped; triggers failover overlay.
   - `connection_restored`: Stream reacquired; clears error states.
   - `track_confirmed`: Target promoted from tentative to confirmed.
   - `track_lost`: Target exited swath or occluded.
   - `buffer_warning`: Backpressure overflow event.
   - `error`: Fatal decoder or pipeline error.

---

## 11. Design System & Theme Alignment

### 11.1 Palette & Design Tokens

The Live Sonar page inherits and extends the maritime design tokens established in `frontend/tailwind.config.ts`:

- **Workstation Background**:
  - Outer background: `bg-bg-primary` (`#F2EFE7`)
  - Panel surface: `bg-bg-surface` (`#FFFCF6`)
  - Elevated / Toolbar container: `bg-bg-elevated` (`#E7ECE8`)
  - Sonar Viewport Core: `#0A0E14` (Sonar dark abyss) with `#131820` border
- **Accents & Status**:
  - Primary Maritime Accent: `#C8523B` (Terracotta Coral)
  - Accent Hover: `#AA4332`
  - Accent Subtle / Active Pill: `#F7E1DA`
  - Success / Confirmed: `#10B981` (Emerald) / `#16A34A`
  - Warning / Tentative / Backpressure: `#D97706` (Amber)
  - Critical Alert / Connection Lost / Debris: `#DC2626` (Red)
  - Science / Swath / Pipe: `#0891B2` (Cyan) / `#0284C7` (Sky)
  - Wreck / Deep Feature: `#7C3AED` (Violet)

### 11.2 Typography & Icon Standards

- **Typography**:
  - UI Labels, headings, button text: `Inter`, sans-serif.
  - Telemetry badges, coordinates, FPS metrics, timestamps, UUIDs: `JetBrains Mono`, monospace.
- **Lucide Icons Used in Workstation**:
  - `Radio`: Live Sonar navigation icon
  - `Waves`: Sonar acoustic backscatter
  - `Target`: Detected anomaly targets
  - `Activity`: Telemetry and FPS signals
  - `ShieldCheck` / `ShieldAlert`: Confirmation and filter status
  - `Crosshair`: Centroid tracking reticles
  - `Compass` / `MapPin`: GNSS navigation lock
  - `Play` / `Pause` / `RotateCcw`: Playback and view reset
  - `Camera`: Forensic snapshot capture
  - `Disc`: Live recording indicator
  - `Maximize2` / `Minimize2`: Workstation fullscreen
  - `SlidersHorizontal`: Filter and threshold settings

---

## 12. Verification & Acceptance Checklist (Frontend Scope)

To ensure strict compliance with `ORIGINAL_REQUEST.md` §Acceptance Criteria:

- [ ] **Route Availability**: Navigating to `/live-sonar` loads the workstation without errors.
- [ ] **Navigation Compliance**: `Sidebar.tsx` shows "Live sonar" under Fieldwork; `Navbar.tsx` reflects active state.
- [ ] **Viewport Modes**: Operator can toggle between `RAW`, `ENHANCED`, `AI`, and `SPLIT` modes.
- [ ] **Interactive Split Slider**: In `SPLIT` mode, operator can drag slider to compare raw vs enhanced/annotated views.
- [ ] **Canvas Performance**: Canvas repaints at native screen rate without creating thousands of DOM elements.
- [ ] **Pan & Zoom**: Smooth mouse drag pan, mouse wheel zoom, fit-to-screen, and fullscreen workstation work.
- [ ] **Real Overlays**: Bounding boxes, track IDs, confidence scores, and trajectory trails render accurately from real incoming frames.
- [ ] **Acoustic Shadow Occlusion**: Wedges render with `Shadow: Detected` or `Shadow: NOT_AVAILABLE`.
- [ ] **No Fake Data Audit**:
  - If GPS is absent, displays `NOT_AVAILABLE`.
  - If sonar range/frequency is absent, displays `NOT_AVAILABLE`.
  - Missing telemetry in the Target Inspection Panel strictly shows `NOT_AVAILABLE`.
- [ ] **Live Metrics Strip**: Displays real-time INPUT FPS, INFERENCE FPS, DISPLAY FPS, LATENCY, GPU, and QUEUE DEPTH.
- [ ] **Backpressure Indicator**: Warning banner triggers when input FPS > inference FPS and frames drop.
- [ ] **Connection State Reliability**:
  - Displays `CONNECTING...`, `CONNECTED`, `RECONNECTING...`.
  - On disconnection: shows `CONNECTION LOST` with last frame timestamp, halts inference, and freezes stream (no faking).
- [ ] **Unambiguous LIVE vs REPLAY**: Red pulsing `● LIVE` badge vs Cyan `⟳ REPLAY` badge clearly displayed.
- [ ] **Replay Controls**: Speed selector, step frame, and timeline seek scrubber function when replaying recordings.
- [ ] **4-Layer Forensic Snapshot**: Captures raw, enhanced, annotated, and JSON metadata artifacts.
- [ ] **TypeScript Build Integrity**: `tsc && vite build` in `frontend/` succeeds with zero errors.

---
*End of Live Sonar Frontend UI Specification (R4)*
