# Scalar intent retirement watermark v1

Task: `COORD-INTENT-GC-WATERMARK-20260917-022`

Decision: **`PASS_SCALAR_INTENT_RETIREMENT_WATERMARK_SCOPED`**

## Method

Container-first deterministic state-machine experiment. Exact source bytes were SHA-256 frozen before execution. The formal runner was invoked once and was not tuned or rerun after its first output. GitHub is only the allocation/publication surface.

## First outcome

| Case | Outcome |
|---|---|
| ID-only bounded history after A(seq1)/B(seq2)/C(seq3), recover exact old A | `NEW_INTENT_ALLOWED` |
| ID-only after GC, same A/seq1 but adapted g4->g5 content | `NEW_INTENT_ALLOWED`, then `APPLIED` -> g5 |
| Watermark candidate after same GC, exact old A/seq1 | `EXPIRED_INTENT`, replay write 0 |
| Watermark candidate, same A/seq1 with adapted content | `EXPIRED_INTENT`, replay write 0 |
| Watermark candidate, label A with fresh seq4/g4->g5 | `NEW_INTENT_ALLOWED`, `APPLIED` once |
| Retained B/seq2 queried with altered transition content | `CONFLICT_INTENT_CONTENT` |

After A/B/C with capacity 2, the candidate retains only B/C and one scalar `retired_through_seq=1`. It does not retain an unbounded tombstone set. Fresh A/seq4 is distinct from retired A/seq1; after applying seq4, the history remains size 2 and the scalar watermark advances to 2.

## Container checks

- `python -m py_compile model.py test_model.py run_experiment.py verify.py`: PASS
- `python -m unittest -v test_model.py`: 6/6 PASS
- formal runner invocation count: 1
- `verify.py`: `PASS_VERIFY`
- source SHA-256 recheck after formal result: PASS 4/4
- formal reruns: 0

## Interpretation

Bounded content-bound history alone forgets an identifier after GC. Once forgotten, an ID-only policy cannot distinguish a stale same-instance reuse from a genuinely new use, and in this fixture the forgotten A/seq1 can be rebound to current g4->g5 content and applied. A monotonic issuer sequence plus one scalar retirement watermark closes that ambiguity for retired sequence numbers while keeping retention finite. Liveness is restored by a genuinely new sequence, not by reusing a retired sequence.

The watermark is an ordered namespace boundary, not a wall-clock timeout. Sequence gaps are rejected by the frozen unit tests.

## Boundary

Deterministic single-process container fixture only. Sequence allocation and watermark provenance are trusted. Capacity 2 is illustrative. No issuer restart/incarnation, malicious rollback, crash/power-loss durability, authentication, distributed consensus, simultaneous linearizability, external effects, performance, or production exactly-once claim.

## Next question

Keep bounded history + scalar watermark fixed and vary only issuer incarnation. If an issuer restarts and its sequence counter resets, test whether binding `(issuer_incarnation, intent_seq)` prevents old retired sequences from becoming valid again without carrying all prior tombstones into the new incarnation.
