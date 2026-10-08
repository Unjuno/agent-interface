# Issue #6580 — formal allocation 01 report

**Disposition: `PASS_METHOD_SCOPED` for finite semantic encoding and independent reconstruction only.** This result does not validate a continuation policy, establish a GUI/model transition lifetime or order, or show useful task progress. It is not a robust-POMDP solver.

## Frozen scope and provenance

Allocation `MODEL-AMBIGUITY-LIFETIME-6580-T0-20261002-01` used the preregistration and freeze recorded on Issue #6580 before formal runs. Base main was `f891ccb0fabac44f43a0d05edfce5fac050e66f0`. The finite candidate crossed three declared lifetime labels (`FULL`, `ZERO`, `EVENT`), two nature/agent move-order information sets, and two receipt conditions for 12 rows; the independent auditor enumerated 56 histories. Six negative-control rows stipulated a parameter-insensitive SAFE effect. Construction included seven corruptions.

Runtime: native WSLc 3.0.1.0, cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, pull/network disabled, one CPU, requested 1G memory, uid 65534. The exact WSLc warning was `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The requested memory limit is recorded; its enforcement is not asserted. No Docker, Podman, GPU, model, GUI, human participant, input authority, or external effect was used.

## Formal stage results

- Construction: one invocation, exit 0; 5/5 tests passed, including all seven frozen corruption controls.
- Candidate: one invocation, exit 0; emitted the frozen 12-row dataset.
- Independent auditor: one invocation, exit 0; `PASS_METHOD_SCOPED`, 12/12 rows, 56 histories reconstructed, six negative controls, zero errors. Candidate raw SHA-256: `469c4590655e5a8ac0633d96a19a49e0dce0930a7b4d5786094e411f724bef1a`.

The auditor independently reconstructed the binary assignment sets: `FULL` holds one value across all three transitions (2 histories); `ZERO` permits a fresh value each transition (8); `EVENT` permits the first two values to differ, then fixes the second value for the third transition (4). Missing/stale evidence retained the same complete sets. The two order labels were checked against the declared information-set strings, and the parameter-insensitive controls agreed.

## Interpretation and residual

This supports only that the frozen implementation represented and reconstructed these declared finite sets and labels, and that the listed corruptions were detected. It does **not** show that an explicit lifetime gate chooses a better or safer continuation than state-set-only, point, or always-YIELD comparators. The move-order axis is recorded as who can condition on the current action; no policy/value optimization or responsive-environment consequence was evaluated. `unsafe_admission` is a fixed false field in this fixture, not a proof about a policy's reachable prefixes.

The source paper distinguishes stickiness and order of play and defines partial stickiness through a declared condition; this allocation is a deliberately small repository-specific encoding, not a reproduction of its numerical RPOMDP example. The next useful validation must add a separately preregistered finite transition game with observation aliasing, action-conditioned nature choices, an independently computed continuation/YIELD decision, and a valid/stale receipt contrast. Do not relabel this result as that follow-up or as a GUI finding.

No stage was retried. `FREEZE.json` retains zero pre-run counters; realized counts are this report. All run receipts, raw output, byte-identical audit input, independent audit output, and SHA-256 manifest are retained alongside this report.
