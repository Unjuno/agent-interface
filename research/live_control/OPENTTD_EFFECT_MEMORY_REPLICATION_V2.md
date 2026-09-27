# OpenTTD bounded effect memory, unchanged live replication

## Frozen replication

V10 was preregistered before execution as an unchanged replication of v9. After
normalizing the supervisor self name and study output name, their effective
sources are identical. The seed991003 save, five-tile L objective, initial state,
all-Astra-medium route, twelve-turn bound, checkpoint grammar, effect memory,
finish classifier and independent scorer are unchanged. There is no retry or
manual intervention.

The first and only v10 execution succeeds. Its semantic route replicates v9:

1. turn5 builds A-to-B;
2. turn6 marks the effect uncertain and inspects without mutation;
3. turn7 uses the retained turn5 evidence, marks observed and builds B-to-C;
4. turn8 marks the second effect uncertain and inspects without mutation;
5. turn9 marks observed and requests independent verification.

The two drag paths differ and neither completed segment is repeated. The
independent score passes target ownership, ordered bidirectional connections,
forbidden tiles and unchanged surrounding state. Observer transitions at103 and
143 change only tiles977..979 and1043/1107. The final37 of180 records retain the
complete state. All17 terminals verify released keys and buttons.

## Replicated envelope

| Endpoint | v9 first live memory | v10 unchanged replication |
| --- | ---: | ---: |
| independent hard success | true | true |
| model turns | 9 | 9 |
| input tokens | 151,853 | 151,842 |
| cached input tokens | 91,392 | 104,448 |
| output tokens | 1,719 | 1,880 |
| repeated completed-segment drags | 0 | 0 |
| durable calls | 34 | 34 |
| exact frames | 44 | 44 |
| verified release terminals | 17 | 17 |
| model wait | 131.034s | 139.465s |
| proposal-to-feedback | 19.048s | 19.491s |
| semantic completion | 153.027s | 160.837s |

Both memories follow `(source turn, inspection count)` values `(5,0)`, `(5,1)`,
`(7,0)`, `(7,1)` and replay pixel-for-pixel against their checked-in planner
images on Windows and WSL.

## Decision and limits

The bounded-memory candidate is2/2 on fresh live executions of this exact task
and2/2 for zero completed-segment repeats. Advance it to a preregistered changed-
geometry allocation. Do not promote it yet.

Two episodes do not estimate a reliable population success rate. They share one
seed, objective, coordinate region and application state. Both require9 model
boundaries and more than151k input tokens, with153–161 seconds to completion;
this is far from human tempo and slower than the earlier one-turn v7 success.
There is no causal speed, token, geometry-transfer or cross-domain claim.
