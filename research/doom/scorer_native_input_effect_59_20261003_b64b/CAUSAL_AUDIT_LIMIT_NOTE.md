# Known terminal and causal-audit limits, archival v4

Read this index-linked qualification first, together with the unchanged
[terminal limitation](TERMINAL_ACCOUNTING_NOTE.md),
[scalar correction](AUDIT_V2_NOTE.md) and [first report](REPORT.md).
V3 received the original assigned nonauthor Root2's explicit
[CONTENT_CHANGES5966283598](https://github.com/Unjuno/agent-interface/pull/6928#issuecomment-5966283598).
That objection is preserved; the author withdrew V3 before any observed
eligible approval. No V1/V2/V3 disposition carries to V4.

The original/formal and corrected-audit PASS objects certify only the checks
actually exercised. V2 adds strict scalar/value checks, but does not establish
adequate causal-order/source-callsite validation. A known-fault archive must
expose this separate limitation as well as the old producer's terminal gap.

The actual nonauthor's retained-data comparison at immutable commit
`92cf265b15613b907b23504a53e4c487be0cad3e` confirms that all16 original rows pass
both verifiers, while seven honestly rejoined copied controls are accepted
by supplied `auditor_v2.verify` and rejected by the separate oracle:

| V2 accepted copied change | Independent rejection |
|---|---|
| Effect marker before FINISH command | EFFECT_AFTER_COMMAND |
| Command before native read | COMMAND_AFTER_READ |
| Sink end before sink begin | SINK_END_ORDER |
| Sample finish bound to a later clock | EXACT_FINISH_CLOCK |
| Read after false readiness | READ_AFTER_READY |
| Clock callsite outside frozen source | CLOCK_SOURCE |
| Cleanup before remaining native operations | LAST_EVENT |

All12 directed controls reject under that separate oracle; the remaining five
type/value controls also reject under V2. The reviewer updated changed saved
rows/scorer/effect files and their size/hash joins, so acceptance is not an
artifact of stale auxiliary-file hashes. This diagnoses verifier coverage,
not fabrication of the original native result or a false original file effect.
No claim of exhaustive causal, malformed-input or adversarial-provenance
coverage follows from either verifier.

The author read the actual immutable saved comparison and its README, confirmed
the original RAW hash/source tuple and inspected the unchanged V2 scalar-only
readiness/callsite checks. V3's verifier blobs equal V2's, so the existing
comparison applies. This qualification makes no claim of a second author
comparison, independent rerun or formal audit. The reviewer's source, changed
artifacts and first outcomes remain attributed to that worker in the
[32-file capsule](https://github.com/Unjuno/agent-interface/tree/92cf265b15613b907b23504a53e4c487be0cad3e/research/reviews/scorer_native_causal_6928_20261003_01a0ff52_5884)
and [12-control comparison](https://github.com/Unjuno/agent-interface/blob/92cf265b15613b907b23504a53e4c487be0cad3e/research/reviews/scorer_native_causal_6928_20261003_01a0ff52_5884/copied-control-comparison.json).
[CAUSAL_REVIEW_POINTER.json](CAUSAL_REVIEW_POINTER.json) binds the actual saved
comparison hash, original source/raw and the seven outcomes. Its elapsed time
is custody metadata, not a performance measurement.

V4 makes only this additive archival qualification, evidence pointer, manifest
and index-link update. All154 V3 targets and the V3 manifest bytes remain
unchanged, including every original source/raw/effect/scorer/audit/deck/freeze
pin, V2 strict-scalar supplement, both first terminal readers and first
publication STOP. No runtime/verifier repair or new oracle is introduced.
No old producer/native/clock/VM/game/model/formal entry point or allocation was
rerun. The repaired service/effect transfer remains source-qualified and the
old terminal5/5/5/6 slots remain descriptive, not actual coverage or promotion
of old fair_v2 as measurement-ready.

Prospective5884/70ab/e0cc seats remain fixed. Fresh exact V4 content agreement,
current-base/planned-tree/actual-requirements/ownership and one conditional
forward main application are separate gates; the author casts no content vote.
The original Root2 objection is not removed or converted to approval. #59/R134,
useful game feedback, held-key physical release, model strategy and matched
recovery/efficiency remain open.
