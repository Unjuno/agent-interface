# Result report — TDCE T0 A02

## Disposition

`PASS_METHOD_SCOPED` for the frozen authored finite model in `FREEZE.json`.

## Observed result

The candidate emitted 336/336 expected rows. The independent raw-only auditor reconstructed all 336 rows with zero errors and zero decision mismatches. Edgewise fallback composition admitted two distinct two-capability joint-loss false continuations: `preserve_sibling_edit` under loss of `semantic_target` plus `native_effect_check`, and `focused_window_action` under loss of `window_identity` plus `focus_stability`. Each corresponding single loss retained a separately qualified route. TDCE produced zero false continuations and zero false stops over 45 feasible rows. Blanket stop rejected 36 feasible rows.

The candidate and auditor each ran exactly once after freeze. Construction controls ran before formal freeze and were repeated after freeze in normal and optimized Python modes; all 15 tests passed in both modes. Formal execution used CPython 3.14.5 on macOS arm64, standard library only. The experiment did not use a container, GUI, model, user data, OS input, external effect, or shared runtime.

## Scope and limits

The tasks, capability losses, route proofs, and contexts are authored finite inputs. The PASS establishes only that the frozen candidate and independent oracle agree over this matrix and the two named witnesses. It does not establish production occurrence, route-proof validity for an application, live task effect, runtime safety, latency, reliability, or product benefit. A01 remains immutable and results are not pooled. No authority or runtime changed.

## Retained artifacts

`FREEZE.json`, `results/candidate.raw.json`, `results/audit.json`, stdout/stderr and exit receipts, construction logs, `RUN_RECORD.json`, and `SHA256SUMS.txt` preserve the run and its provenance.
