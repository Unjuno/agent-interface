# Issue #7741 T0 v1 — result

**Disposition: `METHOD_FAIL_OR_INCONCLUSIVE`; no hypothesis conclusion.** The candidate completed all 504 declared groups. The auditor returned 217 lifecycle-accounting errors; its audit status failed. Although the candidate/auditor summary shows 16/16 peer-vs-frozen reversals, this is not promoted because the independent gate did not pass and the negative-control matching was defective. Control reversal counts were 8 for no-imitation, 8 for the purported partitioned control, and 0 for nonbinding capacity.

## H/T/D/C/U

**H.** Lower task interaction cost can increase optional work and peer-mediated adoption enough to worsen population p95 verified-completion latency under shared capacity; no-imitation and nonbinding/partitioned controls should remove the reversal.

**T.** The exact parameter grid, two topologies, four seeds, 504 groups, candidate, auditor, and event order are in [`FREEZE.json`](FREEZE.json). One local macOS CPython 3.14.5 candidate run was followed by one independent auditor invocation. This finite CPU-only model did not need OrbStack; no user, GUI, runtime service, model, or GPU was used.

**D.** PASS required replay/accounting integrity plus matched negative controls and a preregistered reversal region. Observed: `METHOD_FAIL_OR_INCONCLUSIVE`, 217 audit errors, and nonzero control reversals. Preserve the failure; do not infer a real-world rebound.

**C.** Opportunity elasticity or peer response may be negligible; demand may be fixed; verifier capacity may scale; a nonbinding or partitioned topology may remove cross-principal queueing.

**U.** Bass-style innovation/imitation, task-start probabilities, service time, network topology, and single-queue abstraction are synthetic and uncalibrated. No empirical, production, safety, or human behavior claim follows.

## Evidence

- Candidate raw uncompressed SHA-256: `e45f5b74b68fe17c1a4f456dacc59fa8895d3d80f9320736495ff39a71be1098`.
- Lossless gzip SHA-256: `dcbecabcc8ce4b2c82991bc738465f635deebee4d59dcba742351cb29ee4f1d2`; gzip integrity and decompressed SHA were checked before retaining compressed form.
- Auditor JSON SHA-256: `fd7bbd577d023e3f2448520ef0a647137adbf24d527a4a27a24aacf004938a5f`.
- The audit incorrectly required `service_start` for queued-but-unstarted tasks and compared controls at different verifier capacities. Candidate route probability also saturated to 1.0 conditional on an offered task instead of implementing 0.22. The exact preserved diagnosis is in [`T0_V1_STOP.md`](T0_V1_STOP.md).

The raw candidate is stored losslessly as `candidate-raw.json.gz`; recover with `gzip -dc candidate-raw.json.gz > candidate-raw.json` and verify the uncompressed hash above. T0b is a separate failed construction attempt documented in its own directory.
