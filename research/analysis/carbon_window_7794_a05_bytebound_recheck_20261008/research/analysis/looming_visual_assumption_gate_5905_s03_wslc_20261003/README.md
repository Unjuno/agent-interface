# #5905 S03 — WSLc image-only looming assumption gate

**Terminal disposition: STOP before any invocation.** Main advanced after freeze and before the first WSLc stage. Construction/candidate/auditor/container/retry counts are all zero. See `execution/formal-s03/STOP.json`. Do not rebase or reuse S03.

Fresh allocation `LOOMING-VISUAL-ASSUMPTION-GATE-5905-S03-20261003-01` for Issue #6808, after S02's preserved `STOP_SESSION_ISOLATION_UNAVAILABLE`. S02 is not rerun. This package has a distinct branch, output root, and current-main freeze.

## H / T / D / C / U

- **H:** Two-frame image geometry can identify centered target expansion only when stable anchors and surrounding features independently show coherent radial flow. Visible assumption violations should fail closed; pixel-identical centered-approach and rigid-target-only-growth cases must produce identical UNKNOWN.
- **T:** Twelve deterministic lossless 96×96 PGM pairs: three coherent-expansion positives and nine controls covering common-mode zoom, lateral motion, deformation, partial occlusion, appearance discontinuity, missing/unstable anchors, and a pixel-identical non-identifiability pair. Candidate receives image bytes, timestamps and source epoch only. A separate raw-only auditor reconstructs measurements, hashes, TTC, decision gates, and six corruption controls.
- **D:** Scoped method PASS only with 12/12 reconstructed cases; three positives within 5% TTC error and 200–900 ms simulated release lead; controls never cue; missing/unstable anchors and both identical cases UNKNOWN; and all six raw mutations rejected. Any false cue is FAIL_METHOD. Runtime/source/inventory/audit mismatch is STOP without retry.
- **C:** Hand-built rasters and a simple radial-point detector may make observability easier than natural scenes; two frames do not establish robust temporal tracking.
- **U:** No game/GUI/camera, acceleration, realistic occlusion, model, input, human, latency distribution, task progress, MAP01, or safety/benefit claim. S01 and S02 outcomes are not pooled or changed.

## Frozen execution

See `FREEZE.json` for the authoritative current-main SHA, owner, window, commands, image digest, hashes, gates, and STOP rules. S02 source files and deterministic images are copied unchanged; S02 had zero candidate/auditor/container runs and no scientific outcome, so this is not called an independent replicate. WSLc is the local runtime explicitly requested by the user. It cannot isolate sessions in this environment; require a full empty inventory immediately before each stage. Each invocation is foreground, `--rm`, network disabled, pull disabled, CPU-only, source read-only and output separately mounted. Never inspect, exec into, stop, or remove foreign containers.

The auditor runs once only if the candidate exits 0. No retries or substitute seed. `execution/formal-s03/` is reserved exclusively for this allocation.
