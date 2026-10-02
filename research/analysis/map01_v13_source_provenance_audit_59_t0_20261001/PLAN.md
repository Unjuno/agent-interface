# Issue #59 — current-main v13 source-closure audit

## H / T / D / C / U

- **H:** The v13 MAP01 telemetry-session source set pinned by the retained integration preregistration is either byte-identical on the current-main snapshot or has drifted; a source hash PASS alone does not authorize a live run because the historical allocation is one-shot and its original base is stale.
- **T:** Freeze one exact current-main commit, read the retained `map01_measurement_integration_live_v2_prereg.json` from that commit, independently materialize every path in the union of its `source_sha256` and `canonical_upstream_sha256` maps via `git show`, and compare SHA-256. Run one candidate and, only after successful candidate execution, one independent auditor which recomputes each Git-object hash and validates the inventory against the frozen preregistration.
- **D:** Source-layer PASS only if both maps are structurally valid, the candidate covers their exact union with no missing/extra/duplicate paths, every current-main Git-object hash equals its preregistration pin, and the independent auditor agrees with zero errors. Any changed/missing blob is `FAIL_PINNED_SOURCE_DRIFT`; malformed or incomplete output is `FAIL_AUDIT_INTEGRITY`. Neither outcome is live telemetry validation.
- **C:** The audit uses exact repository Git objects, not working-tree file contents; it does not execute the MAP01 session, ViZDoom, X11, input backend, scorer, or Actions workflow. Historical hash expectations are read from the exact preregistration blob at the frozen current-main commit. A source-stable result can still conceal semantic defects in the source or a stale experimental protocol.
- **U:** No container ownership/lease, exact environment/image, fresh allocation authorization, runtime source provenance file, physical release, scorer cadence, cross-stream clock alignment, useful task outcome, real MAP01 behavior, or recovery-vs-coast effect is established. The historical `map01-measurement-integration-live-02` allocation remains historical; this audit does not reuse it.

## Frozen inputs

- Current main snapshot: `b54ec8fac5d005d510a5787d98b9ad7a24d96923`.
- Expected inventory source: `research/doom/map01_measurement_integration_live_v2_prereg.json` at that exact snapshot.
- Historical integration construction: `research/doom/results/map01-measurement-integration-v2/construction.json` identifies the retired `map01-measurement-integration-live-02` proposal. No formal invocation is made under that allocation.
- Additive source/audit path: `research/analysis/map01_v13_source_provenance_audit_59_t0_20261001/`.
- Collision check before freeze: no matching main path, branch name, or current matching PR was returned by GitHub MCP.

## Execution boundary

Host-only CPython over the already-fetched local Git object database. No network request from candidate/auditor, Docker/OrbStack, model, GPU, ViZDoom/game, GUI, OS input, or Actions dispatch. The shared container inventory remains unobservable and no exclusive live allocation has been granted; this study does not attempt the live probe.
