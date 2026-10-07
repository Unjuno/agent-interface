# A01 review reconstruction — saved-trace outputs

This additive package answers PR #7518 reproducibility review. It does not alter the historical A02 result/audit files.

## H/T/D/C/U

- **H:** Full candidate grids and independent audit outputs can be reconstructed from the exact pinned source and retained candidate/auditor programs.
- **T:** Re-execute the frozen window candidate/auditor pair and the newly frozen availability candidate/auditor pair once each against pinned saved inputs. No game, model, GUI, input, live monitor, or intervention.
- **D:** Input commit `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`; report blob `bff2459036dcdcc44ed100b0c0bc657e1bb8e69a`; event blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`; expected 634 event rows, 218 typed observations, six waits. Raw SHA-256: report `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`; events `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- **C:** Frozen windows 500,1000,1500,2000,2500,3000,4000ms; two adjacent observed numeric decreases trigger at the second when within W; missing/invalid health resets adjacency. Availability compares event top-level capture_ns (asserted equal to nested health.capture_ns) with outer emit_ns. Both clocks cover the same six waits and all seven horizons.
- **U:** Reconstruction of saved retrospective data only; it does not recover historical stdout, add an experimental replication, or establish online utility, safety, causal interruption, task effect, or a live policy.

## Execution and audit

The four source programs were frozen before execution. The availability reconstruction sources and their SHA-256 values are recorded in `PREREGISTRATION.md`; the window candidate/auditor were existing A02 frozen sources, whose SHA-256 values are also pinned there. Executed with Node.js v24.6.0 on the attached Windows workstation (not a container). This was a small, network-fetching JSONL reconstruction, not the containerized live-control experiment; no game/model/input resource was consumed.

- Window candidate: `window_candidate_reconstruction.json` — complete rerun output, clearly not the historical A02 stdout.
- Window independent audit: `window_independent_audit_reconstruction.json` — alternate all-pairs enumeration.
- Availability candidate: `availability_candidate.mjs` and `availability_candidate_reconstruction.json`.
- Availability independent auditor: `availability_independent_audit.mjs` and `availability_independent_audit_reconstruction.json`.

Results: window 42/42 slots independently matched; availability 84/84 slots independently matched. All six wait classifications are retained in every slot: window grid has 21 no-policy and 21 authored-policy slots; availability has 42 per clock, with 28 no-policy and 14 authored-policy per clock. Availability trigger tallies across both clocks: 14 no-policy triggers / 28 no-policy non-triggers; 16 authored-policy triggers / 26 authored-policy non-triggers. The window grid duplicates capture-clock evidence and is not an additional independent episode.

Manifest verification log: the first checksum pass used a slash-containing branch ref in a raw-content URL and returned HTTP 404, so it computed no valid file hashes; no artifact was modified. The check was rerun pinned to immutable commit d2a6b01dd9a263c604e24587c4294ef1ab37a2b7 and all 9/9 manifest entries matched. Both replay outputs recomputed the pinned report/events raw SHA-256 values and expected source counts. Candidate and audit did not agree through shared candidate helper code: auditor uses separate all-pairs enumeration. This only verifies reproducibility/consistency of the stored calculations, not truth of the candidate rule or its usefulness.

## Preservation

Historical `v39_typed_health_window_a02/result.json`, `audit-v2.json`, `v39_typed_health_availability_a02/result.json`, and `audit.json` remain unchanged. The new files are successors/reconstructions, not replacements. Any mismatch, hash change, clock-field divergence, or count error would be retained as STOP/FAIL without retry.
