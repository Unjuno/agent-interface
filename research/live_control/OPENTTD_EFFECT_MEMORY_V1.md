# OpenTTD bounded effect memory, archived-context decision probe

## Failure addressed

The v8 live replication presented bounded before/after/difference panels directly
after its A-to-B drag. Once the model requested an observation-only inspection,
the next planner image replaced those panels with the latest frame and hover
strip. The checkpoint remained bound to turn5, but the visual evidence that had
created it did not. The second inspection replaced the presentation again.

`openttd_effect_memory_v1` retains one unresolved drag. It reconstructs a bounded
row from the original pre-action frame, original post-action frame, latest
inspection frame and amplified action difference. Hover evidence remains above
that row. It stores source turn, observation sequences, frame names and crop box;
it does not accumulate a growing image history. A resolved checkpoint can discard
the memory, and a later drag replaces it.

Replaying frozen v8 turns5..7 produces dimensions1280x1046 after the drag and
1280x1171 after each inspection. The source turn remains5, inspection count moves
0,1,2 and the original before/after frames and crop remain identical. Three
malformed memory controls are rejected. No frozen v8 source or result is changed.

## Preregistered model decisions

Before new model calls, two archived v8 contexts were frozen: exact original
turn7/turn8 prompts, raw baseline outputs, old planner images, new memory images,
model `gpt-6-astra`, effort `medium`, and one new call per context. Only the image
presentation changes. These are separate samples, not paired deterministic model
runs.

| Context | Frozen v8 output | Memory-image output |
| --- | --- | --- |
| turn7 | uncertain, inspect | observed, progress B-to-C drag |
| turn8 | uncertain, stop | observed, progress B-to-C drag |

Both new outputs independently select the same B-to-C points `(641,272)`,
`(673,288)`, `(705,304)` and do not repeat the prior A-to-B points. Total input
tokens are33,655 for the two frozen baseline calls and34,419 for the two memory
calls, a descriptive increase of764. Cache state differs, so this is not a cost
comparison.

## Decision and limits

Advance the candidate to one fresh preregistered live episode with independent
engine scoring. Do not promote it from this probe. The evidence shows a useful
decision change in two retained failure contexts; it does not establish live
correctness, causal improvement, changed-geometry transfer, latency reduction,
token efficiency or human tempo. The live candidate must retain uncertain-effect
mutation gating and explicit typed finish reasons.
