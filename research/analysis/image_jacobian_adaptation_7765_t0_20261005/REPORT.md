# Issue #7765 T0 — retained synthetic comparison

**Disposition: `HOLD_METHOD_DESIGN_CONFOUNDED`.** The frozen auditor returned `PASS_METHOD_SCOPED` against its programmed gate (240 rows, zero replay errors, all goals reached, zero safety violations, and 40.7% fewer aggregate corrections in the gain-drift/cross-coupling subset). That label is not promoted: the online arm used a proportional gain of 0.75 while the fixed arm used 0.48, and the fixed gain was not calibrated on separate training seeds as the Issue requires. The constant-gain condition also favored the online arm (96 vs 162 corrections), consistent with this gain mismatch explaining much of the apparent improvement. This run does not identify a Jacobian-adaptation effect.

## H/T/D/C/U

**H.** The preregistered threshold was >=20% fewer observe/action corrections for online local-Jacobian control on gain-drift and cross-coupling cases, with matched goal outcomes and zero violations.

**T.** Executed 30 paired seeds each for constant gain, gain drift, cross-coupling, and saturation (240 arm-rows). Candidate and auditor each ran once in local CPython 3.14.5 on macOS arm64. Raw event file: 356,420 bytes. Candidate stdout hash: `45455c8bd338925c11231a81bd48801e5890ec1627f33b3bdff6550085665e43`. OrbStack was unavailable for this run: image inspect and pinned-image pull failed because the daemon could not read/lease a content blob (`operation not supported`). Host execution is a documented deviation; no host timing, isolation, or resource-enforcement inference is made.

**D.** The mechanical gate met its numeric threshold: gain-drift + cross-coupling totals were fixed 329 vs online 195 (40.73% fewer); all independently reconstructed terminal outcomes matched; 0 replay errors and 0 safety violations. However, due to the unequal proportional gains and absent separate-seed calibration, the scientific disposition is HOLD, not PASS or FAIL_NO_GAIN. The frozen result is preserved without rerun or relabeling in `formal_01/AUDIT.json`.

**C.** Same paired starts, target identity, observation schedule, action bounds, and hidden-plant rule; fixed-vs-online arm is the intended comparison. The 0.48 vs 0.75 gain mismatch is an uncontrolled difference, not a valid control.

**U.** Finite authored two-dimensional simulator, perfect fresh feature oracle, no delays/occlusion/target loss in formal trials, no GUI or real actuation, no semantic task outcome, and no calibrated baseline. This does not establish transfer or product benefit.

## Reproduction and artifacts

Run `python3 -B runner.py` once, then `python3 -B auditor.py` once in an environment with Python 3. No retries. Both formal commands exited 0. The independent auditor separately regenerates the hidden plant and reconstructs every recorded transition. `SHA256SUMS` binds the frozen inputs, raw output, audit, receipts, and report. Construction tests are in `test_method.py`; they are not the formal result.

The valid follow-up is a new preregistered allocation with baseline proportional gain calibrated on disjoint training seeds, then frozen identically across arms; predecessor raw and audit remain immutable.
