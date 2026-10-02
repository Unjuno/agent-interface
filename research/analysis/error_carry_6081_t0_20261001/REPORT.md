# Issue #6081 T0 — error-carry directional slot compilation

## Disposition

**`STOP_METHOD_INVALID_BASELINE` — no method result is claimed.** The frozen candidate and independent auditor produced 672 rows with zero audit reconstruction errors, but post-freeze review found that the two nearest-direction baselines use maximum dot product rather than minimum Euclidean distance. Because 8-way diagonal command vectors have norm √2 while cardinal vectors have norm 1, the two are not equivalent. The 8-way comparison is invalid. The formal artifacts remain unchanged; no code correction or rerun was made.

This is a synthetic study only. It is not evidence about GUI/game/physical actuation, live safety, or MAP01 progress.

## H / T / D / C / U

- **H:** Under a calibrated constant-displacement finite actuator model, a rational-error-carry schedule will reduce worst-prefix and terminal path error against horizon-wide nearest-direction and independent slot rounding for nonrepresentable intents without safety-envelope or release regressions.
- **T:** Frozen fixture specified cardinal-4 and eight-way-8 legal alphabets; 12 exact rational per-slot intents; horizons 1, 2, 3, 4, 5, 7, 8; and four policies (`horizon_nearest`, `independent_round`, `error_carry`, `no_continuation`). Candidate once, auditor once; both emitted/reconstructed 672 rows. The candidate sees only public cases. A wrong-working-directory auditor launch failed before starting auditor code and created no output; the valid auditor invocation occurred once from the dedicated worktree. No retries.
- **D:** Construction suite 4/4 passed; Python compilation passed. Auditor reconstructed 672/672 rows with zero discrepancies. Raw JSONL SHA-256: `32B3F21A805E52175CDC11F502F4B516079D0E949AB31EA5B33A3C4F66A4BDE8`; audit JSON SHA-256: `D20D558F053E2C27F97A0E27C209ECDAC1666D72A8BCB35CD11C3D18A67FC844`. Aggregate error figures are intentionally not interpreted because the baseline definition is invalid.
- **C:** Exact arithmetic and deterministic fixture eliminate floating-point ambiguity, but baseline semantic validity is a prerequisite and was not met. Five preregistered control classes were declared but not executed in this allocation: unavailable combination, one-slot deadline, omitted-release mutation, calibration mismatch, and held-out nonlinear collision/acceleration.
- **U:** No actual actuator calibration, dwell/latency, acceleration/collision model, focus/authority epochs, concurrent input, perception, or human safety. Docker Desktop Engine did not respond at intake and no shared-container start was authorized; host Python 3.12.10 was used. No network, GUI, game, model, GPU, or physical input was used.

## Why the baseline invalidates the claim

For a desired vector `v` and legal command `c`, nearest Euclidean command minimizes `||v-c||²`, equivalently maximizes `2 v·c - ||c||²`. Maximum `v·c` alone omits the command norm. In the frozen eight-way alphabet, diagonal commands have squared norm 2 and cardinal commands squared norm 1. Therefore the current `nearest()` and auditor `pick()` implementations systematically favor diagonal commands beyond the Euclidean nearest boundary. The auditor's zero discrepancy establishes implementation agreement, not correctness of that metric definition.

The cardinal-4 arm has equal unit command norms, so dot-product and Euclidean nearest coincide there; however, the global preregistered two-alphabet comparison and the unexecuted controls still do not satisfy the declared D criterion. No scoped PASS is issued from this allocation.

## Retained files

- `PLAN.md` — pre-formal H/T/D/C/U and freeze protocol.
- `cases.json`, `truth_oracle.json` — frozen public cases and declared controls.
- `candidate.py`, `audit.py` — candidate and separately written exact-rational reconstruction.
- `test_t0.py` — construction tests.
- `raw.jsonl`, `audit.json` — one formal output and one audit, unchanged.
- `RUN.json` — environment, invocation accounting, defect, and disposition.

## Successor requirements

Any successor must use squared Euclidean distance (including the command-norm term) in independently implemented baseline selection; include a hand-computed diagonal-vs-cardinal boundary fixture; exercise every refusal/release/deadline control; freeze new source and hashes; and keep the nonlinear/collision case held out. This STOP is not repaired by editing or rerunning this allocation.
