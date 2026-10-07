# Issue #5309 A10 — non-isomorphic witness/cost method check

## Disposition

Formal A10 disposition: **`FAIL_AUDIT_VERDICT_COUNT_BUG`**. Candidate and environment each ran once; the frozen auditor ran once and reconstructed all 264 arm rows with zero row errors, but returned `FAIL_AUDIT` because its final gate still compared against the predecessor's 144-row count. No formal retries occurred. A separately versioned read-only audit of the immutable candidate choices/raw/oracle later passed reconstruction; it corroborates retained bytes but does not retroactively turn A10's frozen formal disposition into PASS.

## H / T / D / C / U

- **H:** A witness-aware chooser with a fixed cost budget should gain independently verified completion only when its witness-survival prediction is right and preservation is affordable; it should not falsely complete under misspecification or over-budget costs.
- **T:** 132 deterministic cases over three graph families (cycle-3, branch/merge-4, regular asymmetric-4), all states, correct/misspecified predictions, costs 0/1/2, and prior witness absent/present. Same two admissible actions and equal IG; 264 arm rows. Host CPython 3.14.5. No container, model, GUI, GPU, OS input, network, or authority. Candidate, environment, and auditor were separate CLI processes, but the host filesystem did not enforce oracle isolation.
- **D:** The frozen gate required exact independent reconstruction of 264 rows, zero errors, distinct graph signatures, valid actions/transitions, zero authority, and no unsupported completion. The frozen auditor checked the rows correctly but its stale `reconstructed == 144` threshold produced the formal FAIL. Thus D is not declared passed.
- **C:** All dynamics, predictions and costs are authored and deterministic; this tests a finite method boundary only. Host process separation is weaker than the container mount separation used in A08.
- **U:** No live GUI, natural frequency, calibrated costs/risk, model behavior, runtime, physical input/release, user, safety, or product claim.

## Retained outcomes

The initial auditor output had 264 reconstructed rows, `errors=[]`, 132 cases and zero authority grants, but emitted `FAIL_AUDIT`. Its source checked `reconstructed == 144`; A10's frozen matrix specifies 264. This is preserved as the official first disposition.

The one read-only retained-data audit v2 (`audit_retained_v2.py`) independently recalculated policy choice, graph transitions, witness receipt, commit, decision, topology degree signatures, and arm-by-stratum counts from the immutable inputs/choices/raw/oracle. It returned `PASS_RETAINED_RAW_RECONSTRUCTION`, 264/264 rows, zero errors, and zero authority grants. Descriptive counts:

| Stratum | Generic completion | Witness-aware completion |
|---|---:|---:|
| Prior independent witness present | 66 | 66 |
| Correct prediction, preservation cost within budget | 0 | 22 |
| Correct prediction, preservation cost above budget | 0 | 0 |
| Misspecified prediction | 0 | 0 |

This retrospective read-only check confirms the finite raw behavior and that the observed advantage was confined to the authored correct/affordable stratum. Because the frozen auditor's own verdict gate failed, it is reported as corroboration of retained data, not a formal `PASS_METHOD_SCOPED` or proof of the broader Issue hypothesis.

## Provenance and commands

Base main `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`; allocation `5309-WITNESS-A10-HOST-20261007`; all pre-run source/input hashes are in `FREEZE.md`, and all output hashes are in `SHA256SUMS.txt`. Formal candidate/environment/auditor commands are frozen in `PRE_RUN.md` and each ran once. The v2 audit ran once against already retained bytes; neither candidate nor environment was rerun. A09's separate infrastructure STOP and all earlier A03/A08 evidence remain unchanged.
