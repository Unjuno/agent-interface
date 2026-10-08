# Issue #5352 — formal-01 result

## Decision

`FAIL_SAFETY_OR_REFERENCE_GATE`. The deterministic exhaustive raw and the independent raw-only audit are integrity-valid, and both stateful policies reduce switching in the preregistered boundary subset. However, exact final-mode equivalence against the raw reference fails for both: fixed hysteresis mismatches on 14/155 fresh noncritical traces; minimum dwell mismatches on 54/155. No task ground truth was present, so these are reference-mode divergences, not measured task errors. Do not promote either policy as an accepted default from this rung.

## Formal execution

- Allocation: `planner-hysteresis-5352-t0-20260930-01`; exactly one deterministic enumeration; zero random seeds.
- Frozen main base: `14c1513c7ac516e5dc5b766b4fc99c1b8cbaa2ca`. Source freeze `6463a31cdd89e38e6023c924b182798a99f19b39`; freeze record `3688df544bf2af2a55c55791af2bdf5079ae517e`.
- Runtime: local Windows host, CPython 3.11.9 x64, standard library. 8/8 construction tests passed before formal. Formal runner exit 0; separate auditor exit 0. No Docker/container, GPU, CUDA, model, GUI, or external effect. A host CPU route was used because the shared container owner/lease is unresolved and the local C: volume had no free space; all output was retained in memory then written to this remote evidence branch.
- Coverage: all 8,420 traces of lengths 1–3 over 20 symbols. Canonical raw SHA-256 `90270a631df6887b6240fb5c6db44a9155b15c0c7a9178d3a4d3240755022e1f`, 132960 bytes; stored as base64(gzip(JSONL)) in `raw.jsonl.gz.b64`. Gzip SHA-256 `a522ef59716cd1e812efde6bb7e42a2718ce222870f9aae17d8a317e35cb7d75`.
- Independent auditor: zero raw/schema/reconstruction errors; mutation controls reject decision-bit flip, invalid symbol, and duplicate row (3/3). Full machine-readable receipt follows the raw artifact.

## H/T/D/C/U outcome

- **H:** Partially supported only for this synthetic boundary subset. Raw had 10 mode switches across 8 oscillation traces; fixed hysteresis and minimum dwell each had 4 (60% fewer). This benefit did not satisfy the complete decision gate.
- **T:** Raw, fixed hysteresis (enter 0.7 / exit 0.3), and two-following-fresh-observation minimum dwell compared on identical exhaustive traces.
- **D:** Critical misses 0; stale misses 0; monotone-deterioration traces 36, with maximum crossing delay 0 for all three policies. Final-mode mismatches violate the frozen exact-reference gate (14/155 fixed; 54/155 dwell), so overall FAIL.
- **C:** Synthetic risk symbols and enumerated short sequences only. No calibrated probabilities, learned model, task truth, or interruption-cost measurements.
- **U:** Real confidence calibration, model/token cost, actual task-error implications of conservative over-escalation, longer traces, runtime persistence, workload-specific thresholds and external validity remain unknown.

The result is terminal for this frozen allocation. No threshold/dwell tuning, retry, or replacement run was performed. Keep Issue #5352 open; this finite result motivates discussing whether conservative noncritical over-escalation is acceptable, but does not resolve real planner utility.
