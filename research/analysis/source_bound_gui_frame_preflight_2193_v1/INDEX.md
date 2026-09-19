# Local source-bound preflight index

Branch: `research/source-bound-gui-frame-preflight-2193`

## Scope

Additive research only. No shared runtime, GUI task input, gameplay, provider, or production-performance claim.

## Evidence ladder

1. **Synthetic/container transport** — frame+label generation, receipt consistency, tamper/omission rejection, distribution shift, unknown/yield.
2. **Controlled Windows GUI acquisition** — Tk states captured through computer-use and native GDI client-pixel bytes.
3. **Native GUI local training** — 120 clutter/occlusion frames, per-frame JSON receipts and SHA-256, 354-parameter CUDA CNN.
4. **Native GUI gates** — provenance hash checks, stale/reordered receipt rejection, held-out unknown/yield.

## Latest bounded results

- clean native fixture: 120 frames, 120 unique hashes, CUDA CNN held-out accuracy 1.00, false positives 0
- clutter/partial occlusion fixture: 120 frames, 120 unique hashes, held-out accuracy 0.975, false positives 0
- native GUI unknown/yield: negatives accept 0/21; positives accept 18, yield 1, reject 0
- tampered receipt/frame replacement: rejected by hash gate
- stale/reordered receipts: rejected by step gate

## Not established

- X11/Xvfb transfer (environment dependency stopped)
- DOOM/gameplay transfer
- arbitrary GUI calibration
- token, latency, speed, or human-tempo benefit
- runtime promotion

## Integration next step

Use the native GDI capture and receipt gates as a disposable fixture only. Add stronger occlusion, temporal stale-state scenarios, and a source-bound frame hash before considering any transfer claim. Merge only through a reviewed PR after GitHub API creation limits clear.
