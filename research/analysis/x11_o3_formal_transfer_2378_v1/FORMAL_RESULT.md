# Exact X11 O3 relevance transfer — successor #2378

## H/T/D/C/U

- H: exact 8x8 tile differencing over real X11 pixels can carry generation-bound relevance semantics safely.
- T: Dockerized Xvfb + Tk + python-xlib; 12 fresh sessions × 6 cases = 72 rows; 320×240 XGetImage bytes; 40×30 pixel tiles; current, stale, fresh, critical, and missing receipts.
- D: each row retained before/after X11 bytes, exact changed-tile evidence, receipt generation, decision, expected oracle, and compressed-byte accounting.
- C: fixture-authored relevance only; no DOOM/gameplay, arbitrary GUI, token, latency, model-transfer, or runtime-promotion claim.
- U: PASS requires zero relevant/critical/stale suppression, all intended irrelevant suppressions, all stale/missing full-current fallbacks, nonempty exact changes, and positive avoided bytes.

## Formal result

| metric | result |
|---|---:|
| sessions / rows | 12 / 72 |
| passes / mismatches | 72 / 0 |
| rows with exact nonempty tile change | 72 / 72 |
| current relevant false suppressions | 0 |
| stale full-current fallbacks | 12 / 12 |
| fresh post-shift suppressions | 12 / 12 |
| critical forwards | 12 / 12 |
| missing full-current fallbacks | 12 / 12 |
| avoided compressed bytes | 9,048 |

The earlier PR #2377 remains preflight evidence only. This report is the first result that exercises exact X11 before/after tile differencing and the full 72-row O3 decision block.
