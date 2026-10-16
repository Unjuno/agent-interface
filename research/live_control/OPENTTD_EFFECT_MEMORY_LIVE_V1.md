# OpenTTD bounded effect memory, first fresh live episode

## Allocation

V9 was preregistered before execution. It retains the byte-pinned seed991003
five-tile L task, closed toolbar, pre-action tree transparency, all-Astra-medium
route, twelve-turn bound, typed checkpoint grammar, independent engine scorer and
no automatic retry from v7/v8. The intervention replaces one-turn drag panels
with one bounded unresolved-drag memory: original before, original after, latest
inspection and action difference.

The live harness applies fifteen exact source-pinned transformations to frozen v8
and verifies the v8 hash before execution. It also moves the driver to explicit
finish-kind v2. This is a research harness, not a proposed production loading
mechanism.

## Live result

The first execution succeeds. Turns1..4 discover and prepare the road toolbar.
Turn5 builds A-to-B. Turn6 marks that effect uncertain and performs one
observation-only inspection. The retained turn5 row remains present. Turn7 marks
A-to-B observed and builds the distinct B-to-C segment. Turn8 marks the second
effect uncertain and inspects once. Turn9 marks it observed and requests the
independent score.

The engine passes all four gates:

- target tiles977,978,979,1043,1107 are company-owned roads;
- all four ordered connections are bidirectional;
- forbidden tiles1041,1042,1105,1106 remain clear;
- non-target road/owner state in the49-tile guard is unchanged.

Across171 continuous observer records, index90 changes only tiles977..979 and
index131 changes only1043/1107. The final40 records preserve the complete state.
The model issues exactly two different drags, on turns5 and7, and repeats neither
completed segment.

Effect-memory replay matches the checked-in planner images pixel-for-pixel on
Windows and WSL. Its `(source turn, inspection count)` sequence is `(5,0)`,
`(5,1)`, `(7,0)`, `(7,1)`. The second drag replaces the first memory rather than
growing history.

## Measured envelope

| Endpoint | v7 one-turn sheet | v8 unchanged replication | v9 bounded memory |
| --- | ---: | ---: | ---: |
| independent hard success | true | false | true |
| semantic terminal | verified | typed safe stop | verified |
| model turns | 7 | 8 | 9 |
| input tokens | 116,879 | 133,041 | 151,853 |
| cached input tokens | 52,224 | 91,392 | 91,392 |
| repeated completed-segment drags | 0 | 0 | 0 |
| durable calls | 26 | 30 | 34 |
| exact frames | 32 | 32 | 44 |
| model wait | 94.221s | 116.213s | 131.034s |
| proposal-to-feedback | 12.439s | 13.185s | 19.048s |
| initial observation to semantic completion | 109.034s | unavailable | 153.027s |

All17 v9 runtime terminals verify empty held-key and held-button state. The final
finish kind is `visual_verify`, controller outcome is `verified_success`, and the
driver exits0.

## Decision and limits

Retain bounded effect memory for unchanged replication; do not promote it. It
turns the exact v8 occlusion failure into one independently scored live success,
while preserving uncertain-effect gating and avoiding repeat mutation. It also
adds two turns,34,974 input tokens and43.993 seconds versus v7, so there is no
speed or token benefit.

The sequence now contains two successes and one failure, but v7/v8/v9 are not
three identical interventions: v9 adds persistent memory. One live v9 episode
does not establish causal correctness, a success-rate estimate, changed-geometry
transfer, cross-domain value or human tempo. Next run an unchanged v9 replication;
if it survives, test a preregistered changed geometry before any promotion.
