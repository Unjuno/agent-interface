# Executed cache epoch/dependency boundary check — Issue #2928

## H / T / D / C / U

- **H:** The retained `decision_policy_cache_rung0_v1` monitor cannot distinguish request-origin epoch or dependency-completeness states that are absent from its `CacheEntry`/`Evidence` schema. Holding every represented field at the monitor's KEEP boundary therefore yields candidate KEEP decisions in hidden states where the #2928 replay-safety gate must refuse.
- **T:** One deterministic six-state execution (`request_epoch ∈ {same, changed, missing}` × `dependencies_complete ∈ {true, false}`) against the exact current-main source `research/measurement/decision_policy_cache_rung0_v1/cache.py`, base commit `c7140ca0095554f8af8c8296c8f4de8e8ce26ba5`, source SHA-256 `dfa3ec92ce0f98913cabb5c85e29d4e70cc1d4914d5c62efdd9b84f73d763505`. Host Python 3.12.10 on Windows. Command: `python research/analysis/cache_epoch_monitor_execution_2928_v1/model_check.py`. Docker Desktop was not used because the latest #5074 record has not explicitly released the shared slot. This is not a formal Docker allocation.
- **D:** The candidate returned KEEP in 6/6 states. The independently stated gate permits only `same` + `complete` (1/6), leaving 5 unsafe KEEP recommendations in the declared synthetic replay interpretation. The raw run is labeled `FAIL_REPLAY_SAFETY_BOUNDARY_SCOPED`. The final `independent_audit.py` checked the six-state coverage, recorded rows/counts, required missing fields, source digest/blob, runner/auditor source hashes, and disposition in 13/13 checks; it does not import or execute the candidate.
- **C:** This executes an old, synthetic research monitor, not a production cache, application runtime, or cross-surface lifecycle. Hidden epoch/dependency truth is paired with otherwise identical represented evidence precisely because the subject schema has no fields for that truth. It is a boundary counterexample, not an end-to-end cache operation or an independent runtime implementation.
- **U:** No cache fetch/rebuild, GUI, model, task input, effect, cost, invalidation lifecycle, or production code was exercised. This does not meet #2928's required held-out lifecycle matrix or its PASS gate; it only shows that this historical monitor interface cannot enforce the two added dimensions.

## Retained construction failure

The first independent-audit attempt stopped before producing `AUDIT.json` because the auditor resolved the repository root one directory too high and could not open the source file. See `AUDIT_ATTEMPT_01_STOP.md`. The experiment result was not changed. Only auditor code/provenance checks were corrected; the initial corrected audit-only invocation passed 9 checks, and the final provenance-hardened audit-only invocation passed all 13 checks.

## Artifacts

- `model_check.py`: deterministic candidate execution and row output generation.
- `RESULT.json`: exact six raw rows, source/environment provenance, and scoped disposition.
- `SOURCE_MANIFEST.json`: exact base, runner, auditor, and candidate-source SHA-256 identities.
- `independent_audit.py` / `AUDIT.json`: separate raw-row/hash/count and source-manifest audit.
- `AUDIT_ATTEMPT_01_STOP.md`: preserved initial audit setup failure.

This evidence is additive, preserves prior #5086/#5094 results unchanged, and makes no claim that #2928 is closed.

Before publication, main advanced to `821482e56d5e0e4557fda86da53c12dd44d0e012` (#5098). GitHub readback confirms the subject's latest-main Git blob is still `f4049b6578d0bef344637f2078ead3ae892a01db`, identical to the executed local source blob. The experiment provenance remains the exact `c7140ca...` source revision; the publication branch is rebased to the newer main without changing the experiment bundle.
