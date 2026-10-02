# Issue #6089 T0 — robust observation-horizon method fixture

## H / T / D / C / U

**H.** On this finite one-dimensional plant, an exhaustive reachable-set selector will admit the largest horizon whose every in-envelope state prefix, including the declared release lag, remains strictly below a moving forbidden boundary. It should choose longer horizons in safe corridors and shorten/refuse as uncertainty, boundary motion, or release lag consumes slack. This does not assert an advantage on a live GUI/game.

**T.** Eight deterministic fixtures: narrow versus wide initial uncertainty; a safe long corridor; near-boundary uncertainty; a moving forbidden boundary; invalidated target; zero-slack release; and a disturbance-bound violation used only as out-of-envelope stress. Candidate uses set propagation. A separate raw-only auditor recursively enumerates complete disturbance paths and reconstructs every horizon, every prefix, the nominal-point comparator, fixed-one comparator, and stress disposition. Five byte-level result corruptions are construction controls.

**D.** `PASS_METHOD_SCOPED` requires exact agreement with the independent path enumerator for all eight rows, no admitted in-envelope unsafe prefix, the largest certified horizon in each valid case, fail-closed invalidation/zero-slack behavior, all five raw-record corruption controls rejected, and out-of-bound stress explicitly marked uncertified. Any false in-envelope admission is `FAIL_UNSOUND_TUBE`. This T0 does not test empirical task benefit.

**C.** A short fixed horizon or release-at-deadline may be simpler and as effective. The one-dimensional finite alphabet can make set propagation look more useful than it is; a real controller may have nonspatial semantic hazards or expensive/loose bounds.

**U.** The result is exact only for these authored integer fixtures and declared disturbance sets. It is not a hard bound inferred from samples, GUI/DOOM safety proof, production controller, human-tempo result, or authority to hold input. Out-of-bound stress demonstrates why unsupported bounds must cause UNKNOWN/YIELD in a real deployment.

## Frozen execution plan

- Base main: `702c411c54af2e83b7b5b9640a0ace26be973b45`.
- Branch: `research/reachable-tube-6089-t0-hostcpu-20261002`.
- Allocation: `REACHABLE-TUBE-6089-T0-HOSTCPU-20261002-01`.
- Runtime: local Windows CPython host, CPU-only, stdlib only; no container, Docker/WSLc, network during experiment, GPU/CUDA, model, GUI, game, or input.
- Candidate: one fresh output path; independent audit: one separate Python process reading that raw output; retries/replacements/tuning: zero.
- Formal source/data SHA-256 values and actual outputs are recorded in `FREEZE.json`, `candidate_raw.json`, and `audit.json` after construction tests pass. No output path may be overwritten. Any main change or source/hash mismatch at the final pre-start readback is terminal STOP before candidate.

## Construction tests

Run once before freezing formal bytes:

```powershell
python -m unittest -v test_method.py
```

Construction results are not formal candidate/auditor results. After source freeze, run `run_candidate.py` once and then `run_audit.py` once as separate processes.
