# Issue #5442 T7 — WSLc replay result

## Disposition

`HOLD_PREREGISTERED_CORRUPTION_CONTROL_SCOPE_MISMATCH` — one candidate and one separate auditor ran successfully, and their observed truth table matches the frozen four-case contract. The auditor's own JSON says `PASS_CONTAINER_REPLAY_SCOPED`, but one required D-gate corruption control was not actually implemented as preregistered. Do not promote the auditor's label to an overall T7 PASS. Preserve all first outputs unchanged; no retry or repair run was made.

## Observed candidate result

| Scenario | Intermediate-only | Endpoint-bound receipt |
|---|---|---|
| valid effect | `SUCCESS` | `SEMANTICALLY_CONFIRMED` |
| wrong target | `SUCCESS` | `UNKNOWN` |
| stale pre-state | `SUCCESS` | `UNKNOWN` |
| no-op | `SUCCESS` | `UNKNOWN` |

Candidate WSLc process exit: 0. Raw has exactly four rows. Raw SHA-256: `a8a3115a1945f8b0c466de6d1d2383cce10cf47290b959e47d8cfb60cc4fbf44`.

The independent raw-only auditor ran in a separate WSLc container, exit 0, checked four rows, reported no errors, and rejected four implemented corruptions. Audit JSON SHA-256: `89b6d892c6d4aed872c9f8b1d9a98a30dd442483ec61ddb2f1b84ee854f51f94`.

## D-gate discrepancy found after the one-shot audit

The preregistration required a corruption that changes the intended target. In frozen `audit.py`, the control named `intent_target` executes `x["rows"][0].update(scenario_id="valid_effect:other-target")`. This changes a row identifier in the candidate output; it does **not** change an intended target in the frozen scenario or test target-binding behavior. The raw schema also carries no scenario payload, only the scenario-source digest. Thus the frozen audit JSON's 4/4 control count does not prove the required target-mutation gate.

This is an audit-control/protocol mismatch, not a candidate scientific failure. It was discovered after the sole auditor invocation; no source, raw, audit, or allocation was rewritten or rerun. Any test that mutates frozen scenario intent needs a separately frozen successor allocation and must remain distinct from this retained outcome.

## Scope

The run demonstrates only that this deterministic four-case simulator and its implemented raw-only audit execute in separate offline Python 3.12.14 Linux/amd64 WSLc containers. The authoritative endpoint values are fixture-authored. This does not validate real application observers, GUI effects, runtime authority, safety rates, or product integration. WSLc emitted a swap/cgroup warning; no memory-limit enforcement claim is made. Previous #5442 T0–T6 evidence remains unchanged.

See `START_GATE.md`, `FREEZE.json`, `formal_01/candidate.raw.json`, `formal_01/audit.json`, and the two retained container inspect receipts.
