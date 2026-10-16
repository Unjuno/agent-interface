# OpenTTD bounded drag-effect evidence, first live allocation

## Hypothesis and intervention

The retained v6 episode built the intended A-to-B segment but failed to recognize
that effect. It repeated the same drag twice and never attempted B-to-C. Before
the next execution, v7 froze the same seed991003 save, five-tile L objective,
closed-toolbar state, one pre-action tree-transparency transition, Astra-medium
route, twelve-turn limit, checkpoint semantics and independent engine scorer.

The planner presentation is the intervention. After each pointer drag, the next
model image keeps the current1280x800 full frame and appends three bounded panels:

1. the path region immediately before the drag;
2. the same region after the final observation;
3. an amplified absolute RGB difference.

The panels are descriptive evidence. Pixel change never scores the task; the
source-pinned OpenTTD observer remains authoritative.

## First live result

The first preregistered execution succeeds. Turns1..4 inspect and prepare the road
toolbar. Turn5 selects the southwest-northeast road tool and drags A-to-B. On turn6
the model classifies that checkpoint `observed`, citing new asphalt in the after
crop. It does not repeat A-to-B. It selects the other straight-road direction and
drags B-to-C. Turn7 classifies B-to-C `observed` and requests independent verify.

The engine evaluator passes all four gates:

- all target tiles977,978,979,1043,1107 are company-owned roads;
- the four ordered connections are bidirectional;
- forbidden tiles1041,1042,1105,1106 remain clear;
- every non-target road/owner state in the49-tile guard remains unchanged.

The continuous observer contains122 records and exactly two state transitions.
At index88, tiles977..979 become roads. At index105, tiles1043 and1107 become
roads. The final17 records retain the complete valid state.

## Measured envelope

| Endpoint | v6 retained baseline | v7 effect sheet |
| --- | ---: | ---: |
| independent hard success | false | true |
| model turns | 12 | 7 |
| input tokens | 199,613 | 116,879 |
| repeated same A-to-B drags after first effect | 2 | 0 |
| durable calls | 50 | 26 |
| exact runtime frames | 52 | 32 |
| model wait | 211.916s | 94.221s |
| proposal-to-feedback total | 22.298s | 12.439s |
| initial observation to semantic completion | unavailable | 109.034s +/-50ms |

V7 reports52,224 cached input tokens and1,202 output tokens. All13 program
terminals verify empty held-key/button state. The two effect sheets are1280x1046.
Windows and WSL audits both pass against the preregistered source hashes, typed
proposals, raw model usage, durable calls, frames, observer transitions and final
engine evaluation.

## Decision and limits

Retain the effect sheet for replication. The intervention removed the exact
repeated-work failure seen in v6 and produced the first independently successful
run of this L allocation. The descriptive differences are five fewer model turns,
82,734 fewer input tokens and zero repeated completed-segment drags.

This is one sequential same-task comparison. Model sampling, cache state and game
rendering are not paired, and the prompt now explains the appended evidence. The
result does not establish a causal41% improvement, a latency distribution,
geometry transfer, human tempo or cross-domain benefit. Next run a preregistered
replication and a new geometry/objective before promotion. Measure the extra image
dimensions and provider tokens rather than assuming the crop is free.
