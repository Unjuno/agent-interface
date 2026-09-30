# Retained-analysis audit v2

## H / T / D / C / U

- **H — hypothesis:** the refusal records are an inventory keyed by attempt, so their list order is not semantic. Sorting only `routes.*.refusals` by unique integer attempt should make the retained analysis reproducible without weakening comparisons of values or other arrays.
- **T — target:** frozen parent PR head `d6012bdbeb7b0483d6604d56953a3eb3d7e23f06`; archived package `raw.tar.gz` and published `analysis.json` are inputs and remain unchanged.
- **D — decision rule:** PASS only if archive and every manifest member verify; recomputed v2 analysis matches both frozen analyses after refusal-inventory ordering only; refusal attempts are unique integers; prior STOP, usage projection, source identity, and frozen safety checks hold. Duplicate attempts, changed refusal content, or any other mismatch must fail. Run normally and under `python -O`.
- **C — conditions:** local macOS arm64 / Python 3.14.5 audit of retained files; no fresh live allocation. Docker was not used because other active runs own/stall the Docker daemon. The existing five corruption/effect/review/refusal controls were run in normal and optimized mode.
- **U — uncertainty / boundary:** this is retained-evidence consistency only. It does not repair the caller, prove semantic correctness of model perception, rerun GUI actions, measure autonomous recovery or cost, or clear `HOLD_INTEGRATION_INCOMPLETE`. The parent v1 verifier's failure remains historically true; this additive verifier does not rewrite it or the raw archive.

## Result

`verify_v2.py` passed normally and with `python3 -O`; 617 archived members were checked. `test_audit_v2.py` passed 4/4 tests, covering the retained package, refusal permutation, duplicate attempts, refusal-content sensitivity, and strict ordering of other fields. `controls.py` rejected all five negative controls in both execution modes. `py_compile` passed for all three v2 Python files.

The one discrepancy is exactly the unordered refusal inventory: v1 recomputation produced attempts `[14, 16, 17]`, whereas the frozen published analysis has `[16, 14, 17]`. Canonical ordering restores exact equality; no other field is normalized.

Unchanged input SHA-256:

| File | SHA-256 |
| --- | --- |
| `raw.tar.gz` | `6639d9a146f9e46e6875e06a0742215881efdc3b7571f48d45c7afb4adfaf739` |
| `analysis.json` | `c8e1f8b8258fa477244e5a80484bc675066ea379d4a2a7469f92f8506b4f4be3` |
| `manifest.json` | `6f79e8f1f5643d12a0f1e8b8c7237f22354b0137fe5fdef04e4b35268d114c12` |

Result status: `PASS_RETAINED_MANUAL_GUARDED_DIRECT_SIX_PAIR_AUDIT_V2`; integration remains `HOLD_INTEGRATION_INCOMPLETE`.
