# Sonar Enhancement Method Comparison & Benchmark Report

**Generated**: 2026-09-19 13:15:04 UTC
- **Dataset**: V3 (val split, sequence-isolated)
- **Sample Count**: 2 frames
- **Insertion Point**: `P0`
- **Hardware Platform**: CPU Execution (16-core host)

## Quantitative Benchmark Matrix

| Method | Mean Latency | P95 Latency | P99 Latency | ENL (Looks) | CNR (Target Contrast) | EPI (Edge Preservation) |
|---|---|---|---|---|---|---|
| `identity` | 3.85 ms | 4.86 ms | 4.94 ms | 29.93 | 0.81 | 1.000 |
| `clahe_enhance` | 10.62 ms | 10.84 ms | 10.86 ms | 0.23 | 0.78 | 2.229 |

## Metric Validity and Interpretations
- **ENL (Equivalent Number of Looks)**: Evaluated strictly on homogeneous background ROIs; higher represents reduced speckle variance.
- **CNR (Contrast-to-Noise Ratio)**: Evaluated on centroid-eroded target interior vs surrounding background ring.
- **EPI (Edge Preservation Index)**: High-pass Laplacian energy ratio; identity check yields exactly 1.000.
- **Target CPU Budget**: < 10.0 ms per 640x640 frame for real-time edge integration.

## Registry Traceability
Detailed per-sample records are logged in `EXPERIMENT_REGISTRY.jsonl`.
