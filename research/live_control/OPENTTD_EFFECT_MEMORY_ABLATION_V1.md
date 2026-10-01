# OpenTTD action-effect memory transfer v1

This is the first cross-domain transfer of the action-grounded crop presentation
from the Chromium target ablation. The frozen OpenTTD v9 seed991003 episode is
the source of two already completed drags. Its independent engine observer
recorded target-road transitions at records90 (`977,978,979`, A→B) and131
(`1043,1107`, B→C), and the final scorer verified all road, connection,
forbidden-tile and surroundings checks. No new OpenTTD input occurred here.

For each decision, Image1 was exactly the retained current frame after an
observation-only inspection (sequence36 or44). The three presentations were
current-only, current plus full pre/post frames (sequence29/32 or37/40), and
current plus a bounded before/after/absolute-RGB-difference sheet around the
recorded drag. The prompt, Luna-low model, schema, requested effort, current
PNG and action provenance were held fixed within each context. The model did
not receive the independent engine transition or expected answer. The schedule,
source hashes, pass criterion and zero-retry rule were committed to main before
the single schema preflight and six comparison calls.

| Presentation | Effect decisions matching engine | Safe advance | Input tokens | Submitted images |
|---|---:|---:|---:|---:|
| Current-only | 2/2 | 2/2 | 18,736 | 2 |
| Full pre/post history | 2/2 | 2/2 | 23,748 | 6 |
| Bounded action crop | 1/2 | 1/2 | 19,424 | 4 |

The action crop used4,324 fewer input tokens (18.21%) than full history, but
688 more (3.67%) than current-only. It correctly marked B→C `observed`. For
A→B it returned `contradicted` and `recover_without_repeat`, even though the
independent road transition and the current frame show the completed segment.
The same output classified its memory as `rejected_as_stale_or_misleading`.
The full-history and current-only outputs both marked A→B `observed`.

The A→B sheet contains moving red construction-cost text, a pointer and
highlight, sign labels crossing the road, and a high-contrast difference
panel. It has3,447 changed pixels within the104x72 source crop while the
full frame has155,630 changed pixels. B→C also contains cost text, yet its
bounded sheet was interpreted correctly. These visual differences are
candidate mechanisms for misleading evidence, not an established causal
explanation; the two archived decisions cannot isolate occlusion, ordering or
scene content. The present result rejects this crop presentation under this
condition. It does not reject every action-grounded memory or a crop from a
later clear inspection frame.

The frozen acceptance rule therefore yields `DO_NOT_TRANSFER_CROP`.
Current-only remains the default for these two situations. A future revisit
must first have a current frame that is independently known to be
insufficient, retain action/release/engine provenance, and compare no-memory,
full history and one changed presentation under a newly preregistered same
current frame. Plausible changed presentations are an occlusion-cleared
inspection crop or a bounded sheet with separate semantic landmark context;
they require a new independent engine-checked task and cannot use this
allocation as proof of benefit. Repeat-drag decisions remain unrepresentable
by the schema.

The v1 audit and separately added raw-call retention audit pass. All seven
calls completed once with complete token usage and request plans for
`gpt-5.6-luna`/low, exact prompt/image hashes and one valid decision per call.
The underlying endpoint does not expose independently observed model identity
or monetary cost. Model waits in this tiny sequential archive are descriptive,
not causal latency results. Retention has65 files/56,471 bytes; the original
v9 source and derived PNGs stay separately retained. See the frozen
[`prereg.json`](openttd_effect_memory_ablation_v1_prereg.json) and
[`report.json`](results/openttd-effect-memory-ablation-01/report.json).
