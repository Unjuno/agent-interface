# #5905 S02 — WSLc image-only looming assumption gate

This is a distinct WSLc-runtime successor to #6808's proposed OrbStack S01. It leaves #5905 T0 and S01 untouched. The user has since explicitly directed this research task to use the local WSL Containers runtime; the WSLc image digest below was already cached, so no pull or external service is needed.

## H / T / D / C / U

- **H:** Two-frame image geometry can identify centered target expansion only when stable anchors and surrounding scene features independently show coherent radial flow. It must fail closed on visible assumption violations and return the same `UNKNOWN` for pixel-identical centered-approach and rigid-target-only-growth controls.
- **T:** A deterministic builder emits 12 lossless 96×96 PGM pairs. Three cases contain target expansion plus multi-feature radial scene flow. Controls cover common-mode zoom, lateral motion, deformation, partial occlusion, appearance discontinuity, absent anchors, unstable anchors, and a pixel-identical two-row non-identifiability pair. Candidate uses only PGM bytes, two timestamps and source epoch; IDs are opaque. A separate raw-only auditor reopens images, rebuilds measurements, hashes, TTC/decision gates and six corruption controls. Construction runs on native CPython; the planned formal pair uses two separate WSLc containers, CPU-only, network `none`, `--pull never`, cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, one CPU, read-only source, and separate output mounts.
- **D:** Method PASS requires 12/12 reconstructed cases; all three eligible examples meet ≤5% TTC error and 200–900 ms simulated release lead; visible controls never emit a cue; missing/unstable anchors and both pixel-identical cases are `UNKNOWN`; pair bytes and normalized decisions match; six raw mutations are rejected. Any false cue on a control is `FAIL_METHOD`; source/runtime/inventory/audit mismatch is `STOP` without retry.
- **C:** The hand-built raster family and radial-point detector are deliberately simple; the finite images may make the assumptions much easier to observe than natural scenes. A two-frame gate cannot establish robust temporal tracking.
- **U:** No rendered game, ordinary GUI, camera, acceleration, realistic occlusion, model, input, human, latency distribution, task progress, MAP01 or safety/benefit claim. S01's OrbStack allocation is not reused or regraded.

## Frozen target design

- Issue: #6808; predecessor: #5905 T0 / PR #5920; this package: `research/analysis/looming_visual_assumption_gate_5905_s02_wslc_20261003/`.
- Allocation: `LOOMING-VISUAL-ASSUMPTION-GATE-5905-S02-WSLC-20261003-01`.
- Owner: Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`.
- Intake main: `4d651bee9c89f0084afa6f8b9bea9cd6ac501757`.
- Planned additive branch: `research/5905-visual-assumption-gate-s02-wslc-20261003`.
- Formal output root: `execution/formal-s02/`; candidate and audit output names are unique to S02.
- Frozen raw corruptions: missing row, duplicate row, forged frame hash, forged geometric radius, false SAFE on common-mode zoom, and fabricated release lead.
- No GPU/CUDA, model/provider, network, GUI or OS input. WSLc shares host hardware; CPU/memory configuration is not treated as proof of enforcement.

No formal candidate/auditor invocation is represented by the host construction suite. Formal execution begins only after this source/data freeze is on the dedicated branch, the allocation is recorded on the Issue, and the immediate main/branch/path/output/image/process/container collision checks pass. Candidate max 1, auditor max 1 only after candidate exit 0, retries 0.
