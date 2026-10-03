# #5905 S05 — fresh WSLc image-only looming assumption gate

Allocation `LOOMING-VISUAL-ASSUMPTION-GATE-5905-S05-WSLC-20261003-01` for Issue #6808. S02/S03/S04 are preserved pre-invocation STOPs; none ran a container or candidate. S05 has a distinct base, branch and formal-output root.

## H / T / D / C / U

- **H:** Two-frame image geometry can identify centered target expansion when stable anchors and surrounding features show coherent radial flow; visible assumption violations should fail closed. Pixel-identical centered-approach and rigid-target-only-growth cases must yield identical UNKNOWN.
- **T:** Twelve deterministic 96×96 PGM pairs: three coherent-expansion positives and nine controls for common-mode zoom, lateral motion, deformation, occlusion, appearance discontinuity, missing/unstable anchors and the pixel-identical pair. Candidate gets image bytes, timestamps and source epoch only. An independent raw auditor reconstructs geometry, hashes, TTC/decision gates and six raw corruptions.
- **D:** PASS_METHOD_SCOPED only for 12/12 reconstruction; three positives within 5% TTC error and 200–900 ms simulated release lead; no control cues; required UNKNOWN states; six corruption rejections. False cue is FAIL_METHOD; any runtime/provenance/audit mismatch is STOP without retry.
- **C:** Hand-built images and a simple point detector may overstate observability relative to natural scenes; two frames do not establish robust temporal tracking.
- **U:** No game, GUI, model, input, human, latency distribution, task progress, MAP01, safety or benefit claim. Prior allocations are never pooled/relabelled.

## Execution contract

Authoritative base, image, hashes, window, commands, and STOP rules are in `FREEZE.json`. Local WSLc only; no pull/network/GPU/model. Because sessions cannot be isolated, require a full empty WSLc inventory immediately before construction, candidate and audit separately. Each run is bounded foreground `--rm`, source read-only, distinct output mount. Auditor runs at most once after candidate exit 0. Retry budget 0.
