# Issuer incarnation fence v1

Task: `COORD-ISSUER-INCARNATION-FENCE-20260917-023`

Decision: **`PASS_ISSUER_INCARNATION_FENCE_SCOPED`**

## Method

Container-first deterministic state-machine experiment. GitHub is the canonical allocation/publication surface, not the measured state machine. Exact source bytes were SHA-256 frozen before execution. The formal runner was invoked once.

## First outcome

| Case | Outcome |
|---|---|
| seq-reset baseline, old I1/A/seq1 rebound after restart | `NEW_INTENT_ALLOWED` then `APPLIED`, final g5 |
| incarnation candidate, old I1/A/seq1 after I2 install | `STALE_ISSUER_INCARNATION`, transition write 0 |
| incarnation candidate, fresh I2/A/seq1 | `NEW_INTENT_ALLOWED` then `APPLIED`, final g5 |
| retained I2/A/seq1 with altered transition content | `CONFLICT_INTENT_CONTENT` |

The negative control shows that simply resetting the sequence namespace/watermark to restore liveness after restart also revives old sequence values. The candidate instead installs a new issuer incarnation explicitly and treats sequence numbers as local to that incarnation.

## Container checks

- `python -m py_compile model.py test_model.py run_experiment.py verify.py`: PASS
- `python -m unittest -v test_model.py`: 7/7 PASS
- formal runner invocation count: 1
- `verify.py`: `PASS_VERIFY`
- post-result source hash recheck: 4/4 PASS
- formal reruns: 0

Unit controls also reject future/uninstalled incarnations, non-consecutive incarnation installation, and sequence gaps.

## State bound

The candidate retains only:

- one scalar `current_incarnation`;
- one scalar `retired_through_seq` for the current incarnation;
- capacity-2 content-bound history.

No unbounded tombstone set of retired `(incarnation, seq)` identities is retained.

## Boundary

Deterministic single-process container fixture only. Incarnation installation and provenance are fixture-authored and trusted. No distributed issuer election, malicious rollback, crash/power-loss durability, cryptographic authentication, simultaneous linearizability, external effects, performance, or production exactly-once claim.

## Next question

Keep incarnation-bound sequence identity fixed and vary only how a new incarnation is installed/recovered durably. Test whether an unauthenticated or rollbackable incarnation transition can revive stale authority, versus a content-bound authenticated durable installation receipt.
