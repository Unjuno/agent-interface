# Formal report — Issue #8471 T0 A01

**Disposition: `PASS_METHOD_SCOPED`.** The frozen one-shot candidate and independent audit both completed; all declared finite-method gates passed. This is not a runtime, physical-system, or safety claim.

## Scope

Finite exact-rational method study only. No production/runtime code, physical plant, GUI, actuator, live interface, or safety authority was tested. No container was created: Issue #8471 explicitly scopes this work to the host-only finite model.

## Decision gates

`PASS_METHOD_SCOPED` required exact reconstruction of all 4,096 mode words and policy controls, independently consistent state/product/stability/envelope labels, all unsafe finite words rejected by the strict prefix guard, all 16 minimum-dwell schedules within the declared finite envelope, all common-Lyapunov null rows accepted, and all seven integrity/safety mutations rejected. Equality at a prefix bound of exactly one is not certified. A failure is retained as FAIL; an unresolvable mismatch or incomplete run is HOLD/STOP. These outcomes do not imply operational safety.

## Formal execution record

Frozen formal commands were each executed exactly once in the package directory using CPython 3.14.5 on Darwin arm64, Python standard library only:

- `python3 candidate.py` — exit 0; emitted 4,096 unrestricted rows, 4,096 disturbed responses, 16 distinct dwell schedules, and 4,096 common-Lyapunov rows.
- `python3 audit.py` — exit 0; `PASS`, 4,096 exact independent reconstructions, seven of seven mutations rejected.
- Construction suite before freeze: `python3 -m unittest -v test_construction.py` — 4/4 passed on final source. Earlier pre-freeze failures (wrong expected dwell-schedule count and test matrix-product order) were corrected before freezing; not formal outcomes.

### Results

- Each frozen mode is individually Schur stable. Across unrestricted words, the independent exact second-order Schur test labels 1,248/4,096 products not Schur stable; 129/4,096 trajectories strictly cross the declared infinity-norm envelope 4.
- The multiple-Lyapunov prefix guard certifies 10/4,096 words; none is Schur-unstable and none crosses the declared envelope. It is highly conservative in this finite case. The strict equality control (bound exactly 1) is not certified.
- The hysteresis comparator alone realizes all 4,096 binary mode schedules via extreme inputs, so it does not exclude the destabilizing/envelope-crossing words in this fixture.
- The 10-tick minimum-dwell controller induces 16 distinct schedules over the complete request-word enumeration; all 16 are Schur stable and remain within envelope 4 for the tested initial state/horizon.
- Common-Lyapunov null control accepts all 4,096 arbitrary schedules, all labeled stable.
- With the fixed bounded additive disturbance, the maximum observed absolute coordinate across all words and prefixes is exactly `419173/40960` (~10.234), below the separate finite observation threshold 16. This is only a finite response bound for the declared input/state/horizon; it establishes neither ISS nor robust stability.
- Identity reset and abstract immediate-emergency-overrides-dwell controls were independently checked as method protocol fixtures. No real safety controller or actuator was exercised.

Raw candidate SHA-256: `b0bed2d7e134b30bb60e8696319cbd896576492030fede74fcb6729c0c3e660e`. Frozen source hashes and environment are recorded in `FREEZE.json`. The raw candidate file retains every generated rational state and product.

### Successor qualification

A01 originally represented emergency override as a declared protocol fixture. To test the Issue's no-dwell-delay constraint behaviorally within the abstract method, additive successor [A02](successors/emergency_override_8471_t0_a02_20261008/REPORT.md) enumerates all 20 mode/elapsed-dwell cells and rejects three override-suppression/delay mutations. A01's sources and raw output are not changed. Together, A01/A02 support only the finite method-scoped claim above; Issue #8471 remains open for any eligible source-bound trajectory study (T1), authority-owned envelope, and real-system evidence.
