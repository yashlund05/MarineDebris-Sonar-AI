# Handoff Report: Live Sonar Frontend UI Specification (Requirement R4)

**Agent:** `teamwork_preview_spec_miner_frontend_1`  
**Date:** 2026-09-19  
**Deliverable Path:** `c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_frontend_1\spec_frontend.md`  

---

## 1. Observation

1. **Safety Constraints & Scope (`ORIGINAL_REQUEST.md`)**:
   - `ORIGINAL_REQUEST.md` line 41: Production model `models/detection/sonar_yolov8_fls_trained.pt` must remain byte-identical (SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`).
   - `ORIGINAL_REQUEST.md` line 43: "No fabricated data: No fake detections, fake GPS, fake sonar telemetry, fake confidence values, fake FPS, fake connection states, fake model status. Unavailable values must be null or NOT_AVAILABLE."
   - `ORIGINAL_REQUEST.md` lines 108–125 (Requirement R4): Specifies Main viewport with `RAW`, `ENHANCED`, `AI`, `SPLIT` modes, Canvas/WebGL rendering, AI overlay (boxes, track IDs, confirmation state, acoustic shadows, trajectory trails), Right-side target panel with `NOT_AVAILABLE` for missing telemetry, Live metrics bar, Connection panel, Controls (Record, Snapshot, Toggles, `LIVE`/`REPLAY` indicator), Replay controls (speed, seek, step frame).
   - `ORIGINAL_REQUEST.md` lines 94–98: WebSocket at `/ws/live-sonar/{session_id}` using Redis pub/sub. Bandwidth must remain bounded; preview JPEG/WebP instead of raw multi-megabyte frames.

2. **Existing Frontend Architecture (`frontend/src/`)**:
   - `frontend/package.json` lines 12–29: Uses React 18, Vite 5, Tailwind CSS 3, TypeScript 5.4, `@tanstack/react-query`, `zustand`, `lucide-react`, `recharts`, and has Three.js (`three` and `@react-three/fiber`, `@react-three/drei`) installed.
   - `frontend/src/App.tsx` lines 15–29: Single `BrowserRouter` shell with `AppLayout` wrapping all routes (`/`, `upload`, `surveys`, `surveys/:id`, `models`, `models/evaluation`, `dataset`, `enhancement`).
   - `frontend/src/components/layout/Sidebar.tsx` lines 18–30: Categorizes navigation into `Fieldwork` and `Intelligence`.
   - `frontend/src/components/layout/Navbar.tsx` lines 20–38: Derives page title and subtitle dynamically from current pathname.
   - `frontend/src/tailwind.config.ts` lines 11–51: Maritime palette with warm neutral backgrounds (`bg-primary: #F2EFE7`, `bg-surface: #FFFCF6`, `bg-elevated: #E7ECE8`), text tokens (`#19313A`, `#4F696B`), terracotta coral accent (`#C8523B`), and detection class colors (`gear: #D97706`, `debris: #DC2626`, `wreck: #7C3AED`, `pipe: #0891B2`, `other: #16A34A`, `natural: #475569`).
   - `frontend/src/components/sonar/SonarViewer.tsx` lines 65–83: HTML5 2D canvas drawing routine with `useSonarViewer` hook for pan, zoom, reset, fit-to-screen, and fullscreen.
   - `frontend/src/components/sonar/DetectionOverlay.tsx` lines 63–142: High-contrast bounding box rendering with canonical class colors, selection corner brackets, and monospace confidence/class tags.
   - `frontend/src/components/sonar/BeforeAfterSlider.tsx` lines 77–179: Interactive comparison slider with draggable dividing line, circular grab handle, and clipped layer presentation.
   - `frontend/src/components/detections/DetectionDetail.tsx` lines 188–240: Target detail modal with explicit checks displaying "Location unavailable — navigation metadata was absent from source ping record" and "N/A" for missing dimensions.
   - `frontend/src/api/ws.ts` lines 12–89: `JobWebSocketClient` with auto-reconnect backoff and event dispatching.
   - `frontend/src/store/useAppStore.ts` lines 51–95: Zustand store managing active surveys, detections, filters, viewer modes, and layer toggles.

---

## 2. Logic Chain

1. **Route and Navigation Placement**:
   - Observation 1 and 2 show that `App.tsx` and `Sidebar.tsx` host primary operational pages under `Fieldwork`. Adding `/live-sonar` to `App.tsx` and a navigation item with icon `Radio` to `Sidebar.tsx` integrates the live subsystem directly into the user workflow without disrupting existing survey review pages.
   - Updating `Navbar.tsx` ensures operators have situational awareness with header context ("Live Sonar Subsystem — Real-time acoustic stream detection & tracking").

2. **Viewport Performance & Double-Buffering**:
   - Observation 1 specifies real-time feeds at up to 30 FPS. Observation 2 shows `SonarViewer.tsx` successfully using HTML5 2D Canvas for high performance.
   - To prevent React re-render thrashing at 30 Hz, high-frequency stream events (incoming frames and metrics) are handled via a double-buffered frame ring buffer and driven by a native `requestAnimationFrame` render loop, applying coordinate transformations (`setTransform`) directly.

3. **Multi-Mode Visualization (`RAW`, `ENHANCED`, `AI`, `SPLIT`)**:
   - Observation 1 requires these four modes.
   - Observation 2 reveals existing components (`SonarViewer.tsx`, `BeforeAfterSlider.tsx`, `SideBySideViewer.tsx`) that already implement raw vs enhanced image clipping and comparison. Reusing the slider interaction pattern from `BeforeAfterSlider.tsx` fulfills the `SPLIT` requirement with proven UX consistency.

4. **Overlay Rendering & Physics-Based Indicators**:
   - Observation 1 and 2 establish that targets have track IDs, confirmation states, trajectory trails, and acoustic shadow evidence.
   - The overlay rendering logic extends `DetectionOverlay.tsx` by adding alpha gradient trails ($\alpha_i = (i/K)^{1.5} \times 0.9$), dashed borders for tentative tracks, and down-range occlusion polygons for verified acoustic shadows.

5. **Strict No-Fabrication Enforcement**:
   - Critical Safety Constraint #3 explicitly forbids fake telemetry.
   - All components in the target inspection panel and header telemetry readout strictly map `null` or missing properties to `NOT_AVAILABLE`. Never guess 0.0m or fake coordinates.

6. **Connection Resilience**:
   - Observation 1 requires connection status tracking and explicit behavior on disconnect: halt inference, freeze on last frame, show `CONNECTION LOST` with timestamp.
   - Implementing a state machine in `useLiveSonarStore` with reconnection retries and an error overlay guarantees the operator is never deceived by frozen stale frames pretending to be live.

---

## 3. Caveats

1. **Hardware Native Sonar SDK**:
   - Physical ARIS / Blueprint Subsea hardware devices were not connected during this frontend specification investigation. The UI specification models the native SDK adapter boundary with status `NOT_CONFIGURED` when running without physical sonar hardware.
2. **Backend Live Sonar Service Readiness**:
   - The backend streaming service (`backend/live_sonar/`) is being developed concurrently under R1/R2/R3. The frontend specification defines the strict contract (WebSocket route `/ws/live-sonar/{session_id}` and REST endpoints) matching `ORIGINAL_REQUEST.md` and `api/ws.py`.

---

## 4. Conclusion

The frontend specification for Requirement R4 (**Live Sonar Frontend UI**) is fully documented in:
`c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_frontend_1\spec_frontend.md`

Key outcomes:
- Complete component hierarchy designed for `frontend/src/components/live-sonar/`.
- Dual-buffer Canvas rendering architecture specified for 60 FPS viewport performance.
- 4 viewport modes (`RAW`, `ENHANCED`, `AI`, `SPLIT`) mapped to existing maritime UI patterns.
- Comprehensive overlay engine specified for bounding boxes, track IDs, confirmation badges, fading trajectory trails, and acoustic shadow indicators.
- Strict `NOT_AVAILABLE` telemetry contract enforced across target inspection and live metrics.
- WebSocket message event catalog and Zustand store schema documented for seamless backend integration.

---

## 5. Verification Method

To verify the findings and ensure zero regressions or violations:
1. **Model Integrity**:
   Verify production model SHA256 has not been altered:
   `certutil -hashfile "models\detection\sonar_yolov8_fls_trained.pt" SHA256`
   (Expected: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`)
2. **Frontend Build Verification**:
   Navigate to `frontend/` and run:
   `npm run build`
   (Verifies TypeScript compiles with zero errors)
3. **Spec Document Integrity**:
   Inspect `c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_frontend_1\spec_frontend.md` to confirm all 12 requirement sections, features discovered table, edge cases table, and architectural contracts are present.
4. **Invalidation Conditions**:
   - Any modification of model weights in `models/` invalidates the specification.
   - Any introduction of hardcoded or simulated coordinates/telemetry invalidates Safety Constraint #3.
