# OpenTTD seed-991002 geometry transfer

Status: one preregistered new-save/new-map/new-screen-position episode passed;
dynamic geometry scoring is retained, while the route and speed are not promoted.

## Fixture and question

The earlier guarded road episodes all used target tiles 678..680 from one
canonical save. This allocation fixes seed 991002, selects a guard-safe flat
3x2 rectangle, saves a viewport offset from the target, and restores it in two
fresh processes before any model task run.

The new byte-pinned save has SHA
`2cfdb42ee2f3d1b44e89920387a2299b44072801198cbc76ff88a7609c6c12f7`.
Its target is 465..467, its forbidden row is 529..531, and its exact 7x6 guard
contains 42 tiles. The target is visibly near the top of the screen instead of
the prior central location. The observer-only fixture reproduces all fields in
two fresh restores, rejects an unsaved contract, and starts with no target road.

## Geometry-derived evaluator

`guarded_score_v2.py` derives target, forbidden row and guard IDs from the
restored baseline x/y/width. It rejects changed geometry, missing or unexpected
guard tiles, contradictory overlapping records and malformed types. It also
fails any road or owner change outside the target.

The first probe exposed a missing x/y/width field in the derived contract before
fixture or model use. The corrected probe preserves the archived old positive
and negative outcomes and passes six malformed/change controls on Windows and
WSL. The first fixture audit also incorrectly treated the shorter setup record
as a guard-bearing observer record; that failure is retained and the corrected
audit compares setup geometry separately. The new fixture then passes its
independent preparation audit on both. A later cross-OS replay exposed LF/CRLF
drift in the generated audit JSON; explicit UTF-8/LF byte output restores the
preregistered hash on both systems. All three development failures are retained.

## Preregistered execution

Execution order was fixed as zero-model negative control followed by one
fixed-Astra-medium episode. The negative control made no model or task-input
calls and preserved independent score=false as a typed
`visual_verify_false_positive`. The positive episode received no old target
coordinates and used the same visual task wording and prompt policy.

Fixed Astra inspected the main toolbar, opened Road Construction, chose a
straight-road tool and dragged from root points (737,250) to (673,282). The
prior geometry used a three-point drag around y=383..415. The engine confirmed
owned target roads, bidirectional connectivity, a clear forbidden row and no
surrounding road/owner changes.

| Metric | New geometry | Prior closed-toolbar geometry | Delta |
| --- | ---: | ---: | ---: |
| Hard task success | 1/1 | 1/1 | - |
| Initial observation to semantic completion | 89.097s | 92.377s | -3.280s |
| Wrapper-observed model wait | 75.421s | 79.681s | -4.260s |
| Proposal to useful feedback | 12.032s | 10.605s | +1.428s |
| Model turns | 7 | 6 | +1 |
| Input tokens | 114,177 | 97,729 | +16,448 |
| Exact frames | 32 | 28 | +4 |
| Contact sheets | 4 | 3 | +1 |
| Durable calls | 24 | 20 | +4 |

Provider receipt, provider first token, runtime receipt and OS injection remain
unrecorded rather than estimated.

## Decision

The new geometry succeeds, giving fixed Astra five successes in this narrow
task family: three canonical closed-toolbar episodes, one canonical pre-opened
episode and this one seed-991002 shifted-target episode. Only one alternative
geometry exists, so this is transfer evidence rather than general reliability.

Do not treat the 3.280-second wall-time difference as an interface speedup.
The changed task used more turns, feedback time, tokens, frames and durable
round trips. Shorter sampled model waits masked that additional interface work.
This result strengthens the requirement to judge candidates jointly by
correctness, semantic completion, model wait, useful feedback, boundaries,
tokens and recovery rather than by total wall time alone.

Retain the dynamic geometry-derived scorer for future task allocations. The
next useful allocation should change objective structure or use multiple
preregistered geometries, then collect a matched human control. Repeating this
single geometry would add little.

Windows and WSL task-fixture, scorer and full episode audits pass. Raw evidence
is under `results/timing-envelope-openttd-matched-05/` and
`../openttd_task/results/geometry-01/`.
