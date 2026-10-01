# Issue #6081 T0 — frozen protocol

Allocation: `INTENT-SLOT-6081-T0-20261001-01`  
Intended base main: `6cd70ad4bfad74e11658057bf024918bffb24add`  
Scope: exact synthetic grid only; 17 scenarios; no GUI, game, model, physical input, task, or runtime effect.

## H / T / D / C / U

- **H:** Under an explicitly declared constant-displacement model and legal action dictionary, an error-carry schedule can lower worst-prefix or endpoint error relative to holding one nearest action, at the same fixed number of input slots. This is not assumed under nonlinear, delayed, collision, or uncalibrated dynamics.
- **T:** Freeze 4-way and 8-way directional dictionaries plus a neutral/release slot; rational intent vectors; horizons; switch budgets; release deadline; prefix error envelope; calibration/dynamics status. A compares nearest-to-average direction held for the horizon, B rounds each slot independently, C greedily carries exact accumulated rational error while respecting the switch budget, and D emits only the neutral safe default. The independent auditor uses separately written geometry, finite sumset, schedule, and metric code; it imports no candidate module.
- **D:** `PASS_METHOD_SCOPED` only if at least three exact-N-slot-reachable, non-representable intent cases show strict C improvement over A on worst-prefix or terminal squared error; every compiled C schedule remains within its frozen prefix envelope and switch budget, uses only declared actions, and releases by the deadline; exact-representable/zero controls are correct; and convex-hull, finite-lattice-gap, unavailable-action, nonlinear, calibration, release, and mutation controls are correctly handled. Otherwise `FAIL_METHOD_AUDIT` or a scoped refusal. No live-control inference.
- **C:** Improvement may come from periodic mixing, not error carry itself. Switching cost, actuator nonlinearity, and transient hazards may dominate endpoint approximation.
- **U:** Rational-grid T0 omits rendering, OS input timing, game physics, collision geometry, enemies, focus, simultaneous-key semantics, human perception, and model behavior. Intermediate trajectory safety is not established for a real application. No action is executed by this study.

## Exact preconditions and refusal rules

The requested per-slot rational vector must lie in the convex hull of the declared legal-action vectors. Separately classify the total horizon target as either reachable in the finite N-fold sumset or only feasible in the convex relaxation. The latter remains approximation-only; it must not be mislabeled exact. Outside-hull vectors, unavailable combinations, missing calibration, non-constant dynamics, absent release path, too-short release deadline, and a C trajectory beyond its declared prefix envelope must not emit a compiled action schedule. A common neutral/no-key slot is explicit in each dictionary; it is not evidence that a real actuator has that effect.

## Formal invocation rule

After exact-base, ownership, source-hash, output-emptiness, and branch-readback checks pass, invoke `candidate.py` exactly once and then `audit.py` exactly once on the exact candidate output. No formal rerun, post-output tuning, or live input is permitted. Construction tests ran before freeze. Preserve stdout/stderr, exit codes, timestamps, SHA-256 identities, all raw outputs, and the independent audit. Docker Desktop exists, but the engine probe is unresponsive and a shared container lane is not assigned to this allocation; this T0 is therefore host-only, with that limitation explicit.
