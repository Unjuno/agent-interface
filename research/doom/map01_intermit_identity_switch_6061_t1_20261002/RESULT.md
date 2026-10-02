# Issue #6061 identity-switch T1 result

Allocation `INTERMITTENT-IDENTITY-SWITCH-6061-T1-20261002-01` is a one-shot, synthetic method experiment. The frozen plan and H/T/D/C/U are in [PLAN.md](PLAN.md); exact pre-run identities are in [FREEZE.json](FREEZE.json), and raw outputs are under `results/allocation-01/`.

## Decision

`PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_HOLD`; overall `HOLD_SILENT_IDENTITY_SWITCH_UNOBSERVABLE`. Candidate and independent raw-only auditor each ran once, with zero retries; the auditor returned 20 rows and no errors. Kinematic prediction error was 0.0 in all five scenarios.

The identity+epoch gate released at tick 5 with zero subsequent commanded ticks for the visible identity switch, epoch-only switch, and unknown identity/epoch case. The identity-only gate missed the epoch-only change; the kinematic-only policy continued seven commanded ticks after each observable switch. All five planted corruptions were rejected. This supports only the tested finite synthetic method.

The silent semantic switch and unchanged-target control had identical planner-visible traces. Every continuing policy therefore ran to tick 12, including seven post-switch commanded ticks in the hidden-truth case. The auditor labels that case `UNKNOWN_NOT_CREDITED`; these data cannot show the gate detecting an unobservable change.

## H / T / D / C / U

- **H:** A zero-error kinematic predictor can continue after a semantic target change. A current identity/evidence-epoch fence should stop on observable mismatch or missing evidence. An observationally indistinguishable switch must remain UNKNOWN.
- **T:** Five deterministic 12-tick cases × four policies = 20 trajectories: unchanged control, visible ID+epoch switch, epoch-only switch, unknown ID+epoch, and silent switch. Candidate saw `input.json`; the independently implemented auditor alone received `truth.json`.
- **D:** Required exact tick-5 release for the three observable/unknown discontinuities, no post-boundary commands, expected identity-only and kinematic-only misses, rejection of five corruption controls, and identical silent/control observations classified as UNKNOWN.
- **C:** Perfect one-dimensional synthetic probe with ideal currentness fields. Real interfaces may not expose independent identity/epoch receipts; chunk size and capture cost were not measured.
- **U:** No physical input occupancy/release, real runtime guard, task effect, safety, live MAP01/GUI/model behavior, human tempo, transfer, or product benefit is established.

## Reproduction and evidence

The exact bounded invocation is in [CONTAINER_INVOCATION.md](CONTAINER_INVOCATION.md). The one-shot run used the pre-existing local `python:3.12-alpine` image by immutable ID on OrbStack (`linux/arm64`), with network disabled, read-only root and source mount, 0.25 CPU, 128 MiB, 32 PIDs, and a disposable output mount. It did not inspect, stop, or modify the inventoried pre-existing container or VM; no separate exclusive shared-slot claim was acquired, as disclosed in `FREEZE.json`.

Frozen main base: `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe`. Image: `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`.

| Artifact | SHA-256 |
|---|---|
| Freeze | `161e5b7db7c52374acc9d2087e4dd49ad46a37d9429e3890f1ed3cfbf2f320f9` |
| Input | `237bcfb7301a95f2b48bfa2aedee8abdac60d8e1b8b99c71544b4908abad79d2` |
| Hidden truth (auditor-only) | `ad915910df439bd621f06d3fba3670d5ce0b25f88903194a3e8ec1700e70ba29` |
| Candidate | `db5e6ecb0b78c6f15d62df6ece548c1b9c2b0e4ea129e91bc9e7a9e7dfa4e5a2` |
| Auditor | `9868d560164915e3fe86ac51305e4d29ff5e833f842a45f4bf1e3c0991d44684` |
| Raw output | `367689762143537c538dccd86b70df1cf54e2708f40692e44a301e327dab24b2` |
| Audit output | `09336d35f1c9ce3e49d98ee32e934eb13f90eca5be5619a26f423a9a9676d953` |
| Run record | `0cd1582fdd9dadc81cab2ac9cd7b3db35af10a8f8a03fd8efbb9473aec6f6789` |

An early preparation attempt used an invalid unittest module invocation; a subsequent discovery from the wrong directory found zero tests. Neither invoked the formal candidate, auditor, or container. After correcting the package location, the construction suite passed 8/8 before freeze. These are setup errors, not experimental outcomes.

This additive successor does not revise Issue #6061 T0 or promote synthetic evidence into a live-control claim.
