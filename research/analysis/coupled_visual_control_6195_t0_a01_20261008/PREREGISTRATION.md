# Issue #8470 T0 A01 — frozen finite composition test

Status before invocation: `FROZEN; CANDIDATE_NOT_RUN; AUDITOR_NOT_RUN`.

## H / T / D / C / U

- **H:** For this finite nonnegative two-axis system family, passing each component's isolated infinity-row-gain check is insufficient: at least one coupled composition exceeds feature bound 2. A conservative composition screen that includes cross-axis, delayed-observation, hold-duration, and release-tail gains will refuse every unsafe/out-of-envelope case and certify at least the uncoupled and bounded delayed positive controls.
- **T:** One exact-rational candidate run over the eight immutable cases in `cases.json`, followed by one separate exact-rational auditor run over the candidate raw. The model contains current-state, delayed-state, actuator/controller, release-residual, estimator-error and disturbance terms; a fixed finite delay/jitter schedule; actuator saturation; requested versus maximum hold duration; exact finite trajectories; and an induced-infinity small-gain envelope. The envelope conservatively sums current, delayed, actuator/controller, and release-loop gains and requires maximum row sum < 1. The feature bound is 2; candidate uses no float.
- **D:** `PASS_METHOD_SCOPED` only if the auditor reconstructs every raw row/trajectory/gain matrix; C01 and C03 certify; C02 has every isolated component below unit gain yet is refused and crosses bound 2; C04 is reported as a bounded nonconvergent gain-envelope boundary and is not certified; C05 is a stable envelope conservatively rejected (not called unstable); C06 release lag is included and refused; C07 over-cap hold is refused; C08 finite estimator/disturbance feature escape is refused; all three gain-matrix mutations (omit cross coupling, omit release path, understate a gain) are rejected; no certified case crosses the bound. Otherwise preserve the first candidate/audit result and classify as the corresponding failure/hold. No retry.
- **C:** Direct finite-horizon reachability may be simpler and stronger for this small family. The sufficient gain envelope may reject useful stable systems. Component composition may add no useful decision beyond the exact trajectory gate.
- **U:** This is a synthetic linear recurrence. The gain matrix is an explicit finite envelope, not an empirically identified subsystem contract. The scalar release recurrence and prescribed delay schedule do not establish arbitrary jitter/switching stability, real actuator behavior, GUI semantics, irreversible-effect safety, model behavior, live task success, or usefulness on the product.

## Frozen mechanics and expected classifications

All values are exact rational strings in `cases.json`; max feature uses infinity norm; gain-envelope status uses the exact nonnegative 2×2 determinant-at-one criterion. The candidate recurrence is: observe the scheduled delayed state plus the fixed estimator-error vector; apply the frozen controller and per-axis saturation; scale admitted control by requested hold duration (only when positive); update the two feature coordinates from current state, delayed state, actuator command, residual from the prior release lag, and fixed disturbance; carry the residual as `release_factor × admitted_command`. Requested holds above the case limit are hard-invalid and may never certify.

| Row | Required label |
|---|---|
| C01 | CERTIFIED uncoupled positive control |
| C02 | all isolated blocks pass; UNSTABLE_ENVELOPE; NO_COMPOSITION_CERTIFICATE; trajectory crosses 2 |
| C03 | delay schedule max 2 with shared actuator and release; CERTIFIED within finite bound |
| C04 | BOUNDED_NONCONVERGENT_ENVELOPE; NO_COMPOSITION_CERTIFICATE |
| C05 | STABLE_ENVELOPE but NO_COMPOSITION_CERTIFICATE (conservative rejection) |
| C06 | release path included; NO_COMPOSITION_CERTIFICATE |
| C07 | held-input cap invalid; NO_COMPOSITION_CERTIFICATE |
| C08 | finite disturbance/estimator trajectory crosses 2; NO_COMPOSITION_CERTIFICATE |

Auditor mutations are derived from a row with both off-diagonal coupling and nonzero release gain. One mutates the reported gain matrix by deleting a cross-axis term; one drops the release contribution; one understates a gain entry. The auditor must reject each mutated report against its independently reconstructed exact matrix.

## Inputs and execution boundary

- Source base intended for evidence branch: latest verified `main` SHA recorded in `FREEZE.json`.
- Candidate: `candidate.py`; independent auditor: `audit.py`; fixed inputs: `cases.json`.
- Construction suite (`test_candidate_contract.py`, `test_auditor_contract.py`, `test_fixture_construction.py`) passed before freeze. These tests do not count as formal candidate/auditor invocations.
- Formal commands, each exactly once, in this directory:

```text
python candidate.py cases.json
python audit.py cases.json CANDIDATE.stdout.json
```

- Python 3.12 standard library only, exact fractions, CPU-only. No game, GUI, model, GPU, external service, or user data. No Docker/WSLc command is necessary for this in-process arithmetic method test; the WSLc-specific ownership gate remains untouched. This disposition is not container performance or resource-isolation evidence.
- Candidate raw and auditor output/exit/stderr are retained separately. Any formal invocation failure consumes the one-shot result; do not repair and rerun under A01.
