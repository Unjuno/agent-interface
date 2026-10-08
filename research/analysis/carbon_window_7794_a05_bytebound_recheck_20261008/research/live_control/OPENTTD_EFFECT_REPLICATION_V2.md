# OpenTTD bounded effect evidence, unchanged replication

## Replication result

V8 was preregistered as an unchanged same-task replication before execution.
After normalizing only the study and self-source names, the v7/v8 supervisor logic
and prompt are identical; v8 has two additional trailing blank lines, which are
part of its frozen source hash and have no runtime semantics.

The replication builds A-to-B once on turn5. The first effect sheet shows a changed
corridor, but the model marks it `uncertain` because the sign labels, cost popup
and construction highlight obscure continuity. Turns6 and7 use observation-only
pointer moves and dwell samples to clear those transients. Turn8 still cannot
distinguish the road from terrain shadow and issues a typed safe stop. It never
repeats A-to-B and never mutates B-to-C.

The independent evaluator returns false because only tiles977..979 are built.
Forbidden and surrounding tiles remain valid. Across147 continuous observer
records, index82 is the only transition; the partial A-to-B state remains stable
for the final65 records. All15 runtime terminals verify released input.

| Endpoint | v7 first live | v8 unchanged replication |
| --- | ---: | ---: |
| independent hard success | true | false |
| semantic terminal | verified success | typed model safe stop |
| model turns | 7 | 8 |
| input tokens | 116,879 | 133,041 |
| cached input tokens | 52,224 | 91,392 |
| repeated A-to-B drags | 0 | 0 |
| A-to-B inspection-only turns | 0 | 2 |
| durable calls | 26 | 30 |
| exact frames | 32 | 32 |
| model wait | 94.221s | 116.213s |
| proposal-to-feedback | 12.439s | 13.185s |

The candidate therefore has1/2 same-task hard success and2/2 prevention of the
specific repeated completed-segment mutation. Hold it rather than promote it.
The next interface should retain the original action-effect evidence across
bounded inspection turns and reduce sign/transient occlusion. It must preserve
the current rule that uncertain evidence cannot authorize a new mutation.

## Finish-outcome defect and repair

The frozen v8 raw failure document labels this explicit safe stop
`bounded_turn_limit`. `openttd_finish_outcome_v1` classified every `abort.json`
that way, even when the supervisor's persisted reason began `typed model safe
stop`. The raw artifact and defect are retained.

`openttd_finish_outcome_v2` replaces filename inference with a required
`finish_kind`: `visual_verify`, `bounded_turn_limit`, `typed_model_safe_stop` or
`supervisor_cleanup`. Independent task success and controller outcome are stored
separately. This matters when a controller safely stops while hidden independent
state already satisfies the task. Twelve valid controls and four malformed-kind/
score controls pass. Replaying v8 now yields `typed_model_safe_stop`; replaying
v7 remains `verified_success`. New drivers use this candidate; frozen v7/v8 files
remain unchanged.

## Limits

These are two sequential episodes on one seed and one objective. The result does
not establish geometry transfer, a latency distribution, causal token reduction,
human tempo or a cross-domain benefit. It does show that one-frame local effect
evidence is insufficient under variable occlusion, while checkpoint gating avoids
unsafe repeated mutation in both observed cases.
