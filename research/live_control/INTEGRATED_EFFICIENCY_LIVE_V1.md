# Integrated efficiency live result v1

The preregistered `integrated-efficiency-live-01` allocation returns **RETAIN**.
Plain, ephemeral and persistent each submitted all six task tokens exactly once
under the independent append-only scorer. Persistent reused layout-A references
for tasks 2/3, refused the old field reference as `MISSING` with zero pointer
admissions on task 4, repaired once from the current layout-B image, and reused
the replacement on tasks 5/6. Every task recorded two button-down admissions
and every checked program ended with empty verified input release.

| Arm | Actual cumulative input tokens at task 6 | Planner generations including fresh preflight | Image calls | Six-task elapsed | Image-model wait |
|---|---:|---:|---:|---:|---:|
| Plain batched visual program | 63,128 | 7 | 6 | 56.412 s | 41.318 s |
| Compiled ephemeral | 63,779 | 7 | 6 | 73.238 s | 48.742 s |
| Compiled persistent | 26,563 | 3 | 2 | 44.131 s | 15.460 s |

The first measured task index where persistent cumulative input tokens fall
below both references is task 2. At task 6 it uses 57.9% fewer input tokens than
plain and 58.4% fewer than ephemeral within this exact allocation. Its elapsed
time is descriptively 21.8% below plain and 39.7% below ephemeral. This is one
fixed sequence, so the timing is not a rate estimate or a general speed claim.

The input path itself remains stable across arms: acknowledgement to the next
captured observation has medians of 99.944 ms (plain), 99.299 ms (ephemeral) and
99.250 ms (persistent). Persistence reduces model waits and image generations;
it does not improve the approximately 100 ms local feedback interval in this
fixture. Persistent also performs more conservative local checking: 136 local
observations and 114 durable calls versus 105/36 for plain and 129/96 for
ephemeral. The lower end-to-end time therefore comes from avoiding four image
model calls despite that additional local work.

Schema acquisition is fully charged. Each independently cold arm made one fresh
no-image Luna-low endpoint preflight in a separate empty cache, followed by
6/6/2 image-backed grounding calls. Across all arms this is 17 actual calls,
153,470 input tokens, 4,864 cached input tokens (already a subset of input),
2,435 output tokens and 837 reasoning-output tokens. Call IDs are unique and all
raw model, frame, runtime and submission records remain in the result tree.

The pre-formal composed runner found an eighth integration issue: the runtime's
exported submission history materializes at session finish. Probe-01 completed
all GUI actions but provisionally counted every submission as zero. That failed
result is retained. The smallest repair reconciles the finalized append-only
history to preserved task/source records by task ID; zero-model probe-02 then
completed all 18 tasks and passed the same protocol. Because this was found and
fixed before preregistration, the formal allocation was not changed.

This result supports persistence for this desktop workflow. It does not prove
population reliability, broad GUI generality, human-level speed, cross-platform
behavior or normal-map DOOM completion. The next gate is the separately scoped,
continuously advancing Freedoom MAP01 experiment already defined in the plan.
