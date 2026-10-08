# Issue #6590 T0 — finite spatial-block method experiment

This T0 tests the proposed evaluation method, not visual-model efficacy. It generates a new, synthetic 8×8 position field with a uniform positive control and a predeclared local-failure hotspot; a raw-only independent auditor reconstructs every row, compares a within-position random diagnostic with leave-one-spatial-block-out rates, checks identity/position leakage, and makes empty support `INSUFFICIENT`.

## H / T / D / C / U

- **H (Issue-level T1):** a position-random held-out estimate overstates positive ACCEPT in disjoint position blocks by at least 0.20 absolute for a fresh #4752-style diversified-position task. The old #4752 PASS is not changed.
- **T (this T0):** a no-model finite method control: 8×8 centers, four 4×4 blocks, 50 positive and 50 negative rows per center for each of two authored fields (12,800 rows total), one fixed renderer variant, distinct row/source/noise identities. The random split is deliberately diagnostic-only; the confirmatory statistic is leave-one-whole-block-out. Block geometry, salts, support floors, and gates are frozen in `FREEZE.json` before the single candidate and single independent-auditor invocation. No model fit, GUI, GPU, or old allocation is run.
- **D:** `METHOD_PASS` only if the raw-only auditor reconstructs every row; the uniform field has zero block-rate range; the declared hotspot is the worst block and random-minus-worst-block positive ACCEPT is ≥0.20; block folds have no row/source/noise/position overlap; random split is explicitly diagnostic-only; all blocks meet support; and empty support yields `INSUFFICIENT`. Otherwise `FAIL_METHOD` or `HOLD_AUDIT_INTEGRITY`.
- **C:** this exact generated field has authored, fixed outcomes. One renderer, one grid and one hotspot do not estimate deployment behavior or spatial correlation in real interfaces.
- **U:** no trained model, GUI pixels, human, real application effect, calibration, safety/authority, causal benefit, or general visual robustness is tested. A method pass only validates the T0 aggregation/split controls; the issue-level T1 remains separately gated and needs a fresh WSLc CPU allocation.

## Prior evidence retained unchanged

The merged #4752 source report records treatment held-out positives at 200/400 vs control 0/400, with translation A 0/200 and B 200/200. Its saved independent raw-only audit in the frozen Python 3.11.2 / NumPy 1.24.2 environment has `errors=[]`. The raw-byte bundle for #4814 has SHA-256 `4edc2022cd1b911a57f702c3d3ccbb7208c42afc90721dd40001986197fd81c7`, 16 members / 4,168,206 expanded bytes, and a saved `PASS_RAW_BUNDLE_RECONCILES_MANIFEST`; #4814's separate CNN efficacy result remains FAIL. Exact old evidence and a host-only version-drift re-audit are captured, without modifying those originals, in `PRIOR_EVIDENCE_RECONSTRUCTION.json`.

Read-only compatibility diagnostic: running #4752's frozen auditor on this macOS host (CPython 3.14.5 / NumPy 2.5.2) reproduced the same decision counts but reported 11 `prediction_recompute` differences out of 2,400. Maximum absolute delta was one float32 ULP (`1.1920928955078125e-7`) against the frozen `1e-7` tolerance; no ACCEPT-threshold decision changed. This environment-drift diagnostic is retained as a limitation and does not overwrite or upgrade the original Docker audit. No #4752 fit was rerun.

## Reproduce

Run the construction suite with `python3 -B -m unittest discover -s research/analysis/spatial_block_position_6590_t0_20261002 -p 'test_*.py' -v`. The formal T0 commands, environment, counts, audit and source hashes are in `RUN_PROTOCOL.md`, `FREEZE.json`, and the append-only `results/` directory. T0 is host-only because WSLc is unavailable in this macOS task and the shared OrbStack lane is still unassigned; this is not T1's required WSLc/container evidence.
