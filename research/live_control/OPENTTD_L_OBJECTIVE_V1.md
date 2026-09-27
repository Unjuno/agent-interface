# OpenTTD five-tile L objective, allocation v1

Status: the model-free fixture and negative controls pass; allocation v1 retains
a pre-input harness failure, while corrected allocation v2 reaches a false
visual completion that the independent engine score rejects.

## Objective change

Seed 991003 fixes a five-tile L path: three tiles from A to the shared B corner,
then three tiles from B to C. Four other tiles inside the 3x3 square must remain
road-free, and a 49-tile guard must preserve road and owner state. This requires
two directional segments and a correct shared corner rather than another
straight-road placement.

The byte-pinned save SHA is
`c91ea76b4dc8c280f98de2e3a4c9b34d6033c833a34fc401bd0c076a15b4bc5b`.
Two fresh restores reproduce target tiles 977, 978, 979, 1043 and 1107,
forbidden tiles 1041, 1042, 1105 and 1106, all four ordered edge queries and
the complete guard. Windows and WSL audits pass. An unsaved observer refuses to
start, and the observer contains no construction or viewport mutation calls.

## Retained failures

The first fixture-generation attempt used an unsupported GameScript API version
and its cleanup path lacked a `subprocess` import. The raw failed process output
is retained under `results/l-geometry-01-development-failure/`. Correcting both
produced the audited fixture above.

The preregistered execution order was a zero-model negative finish control then
one fixed-Astra-medium allocation with no retry. The negative control passed:
independent score remained false, the result was typed as
`visual_verify_false_positive`, and no durable task input was issued.

The positive allocation obtained one valid model proposal to hover the apparent
road toolbar icon. Before that pointer move could execute, the new driver added
an explicit request `id` to a durable submit. `durable_submit_v4` correctly
rejected it because the journal exclusively assigns unique identities. The
supervisor retained the driver traceback and stopped without retry. No road
mutation or semantic success is claimed.

## Corrected allocation v2

The v2 sources and a fresh result root were preregistered before another
zero-model negative control and one fixed-Astra-medium execution. The negative
control passed. The live path then executed eight action proposals and a ninth
visual verification proposal without harness failure.

The model drew two segments and declared that the L was complete. Independent
engine evidence disagreed. The B-to-C leg was correct: tiles 979, 1043 and 1107
were owned road tiles, with both ordered connections present. Tiles 977 and 978
on the A-to-B leg remained empty. Instead, tiles 912..915 changed to road one map
row above that leg. All four forbidden tiles remained clear, but surrounding
preservation failed. This is a typed `visual_verify_false_positive`.

The model requested visual verification 148.339 seconds after initial
observation detection. Wrapper-observed model wait was 130.847 seconds and
proposal-to-useful-feedback time totaled 16.765 seconds. It consumed 146,736
reported input tokens, 39,168 cached input tokens, 42 exact frames, four contact
sheets and 32 durable calls. There is no semantic-completion time because the
hard task gate failed.

The first drag ran through points (705,224), (673,240), (641,256), near the
visible sign-label height. The resulting off-target engine row supports a
target-binding-error hypothesis, but the runtime did not instrument the causal
mapping, so this is not a proven cause.

## Decision

Keep both frozen allocations. V1 is a harness failure and v2 is a real task
failure. Do not promote the fixed route. Before another live allocation, test a
generic magnified changed-region feedback candidate on the archived trace to see
whether the misplaced first leg becomes visually distinguishable without using
the engine oracle. A later fresh comparison must preregister that presentation
change and retain full-frame fallback.

That archived diagnostic is now complete. The visual-only composite preserves
the full current frame exactly and appends two-times before/after crops around
the pointer path. It adds 40,680 PNG bytes. With the same prompt and fixed
Astra-medium, both the full-only and composite conditions answer `uncertain`;
reported input is 15,279 versus 15,805 tokens. The crop does not improve the
judgment and is rejected as a standalone candidate.

The full frame already elicits appropriate uncertainty when the planner asks for an
explicit A-to-B alignment assessment. The next candidate should therefore make
semantic subgoal status part of the action contract: after a mutation, the
planner must mark the expected effect observed, contradicted or uncertain before
another mutation is admitted. This can reuse the existing model boundary rather
than add a new crop or call.

## Semantic checkpoint live allocation

A third preregistered allocation adds that contract while keeping the seed,
task, model and durable driver fixed. After its first drag, Astra reports the
A-to-B result `uncertain` for five consecutive inspection turns. No later task
mutation starts and the earlier false visual verification does not recur. On
turn 11 the model safely stops because foliage and labels still prevent tracing
all three tiles.

This improves failure semantics, not task correctness or efficiency. The task
still fails because the first drag built tiles 912..915 outside the target. The
safe-stop proposal arrives after 185.761 seconds, with 165.704 seconds of model
wait, 19.057 seconds of feedback, 182,284 input tokens, 42 frames, eight contact
sheets and 40 durable calls. Compared with allocation v2, it adds two turns and
35,548 input tokens.

The frozen checkpoint v1 parser also applies its observed-only verification rule
to `stop`, incorrectly rejecting the safe uncertain stop as an exception. The
result remains frozen. `semantic_checkpoint_v2.py` narrows that rule to verify;
its probe accepts the archived turn-11 stop while preserving the uncertain
inspection and contradicted repair paths.

## View-only recovery feasibility

The remaining uncertainty has an app-provided recovery route. The official
OpenTTD manual documents Ctrl+2 as tree-transparency toggle. A preregistered
zero-model shared-runtime probe executes that chord, changes 398,590 of
1,024,000 screenshot pixels and exposes the ground around A/B/C. Independent
engine state remains entirely unchanged, including all targets, forbidden tiles,
49 guard tiles and save bytes.

Retain this as an app-specific learned view optimizer. It is not yet available
to the planner schema and has not recovered a fresh model task. The next
candidate should expose a typed `openttd.transparent_trees` view method under an
uncertain checkpoint, expand it locally to the verified chord and keep the
universal keyboard/pointer fallback.

## Typed view allocation and calibration

Allocation v4 exposes that method under the uncertain checkpoint. The zero-model
negative control passes, then fixed Astra uses the typed method on turns 6, 8
and 10 after its turn-5 A-to-B drag. It starts no later task mutation and safely
stops on turn 12. Independent evaluation finds no target, forbidden or
surrounding road-owner change. The method therefore improves failure containment
over v3's four off-target roads, but task correctness remains false.

The allocation uses 198,746 reported input tokens, including 117,504 cached,
165.558 seconds of model wait, 17.935 seconds of proposal-to-feedback time, 45
exact frames, 44 durable calls and five contact sheets. Three calls to a toggle
alternate transparent, opaque and transparent presentation. This exposes a
contract error: a typed method should describe a postcondition and track state,
not publish a repeatable toggle.

A preregistered zero-model drag calibration then isolates six vertical offsets
on fresh restores. Offset -16, the v2 path, builds surrounding tiles 912..915.
Offsets -12, -8, -4, 0 and +4 all build the intended A-to-B tiles 977..979 and
change no surrounding tile. Thus v4's offset-0 coordinates are valid in the
fixture. A second diagnostic keeps offset 0 fixed and compares selection plus
drag in one program, an immediate program boundary and a 15-second boundary.
All three build 977..979. Program separation and the sampled delay do not explain
v4's zero-effect drag.

The first calibration harness attempted the documented Shift+F8 shortcut, but
the shared runtime rejected F8 as an unsupported key before the drag. That raw
failure is retained. The corrected calibration uses the already measured visible
toolbar coordinates. Its first frozen audit compared a summarized finish event
with the full evaluation document; the failed audit is retained and a corrected
cross-OS audit compares their shared fields.

`semantic_checkpoint_v4.py` now represents the method as
`openttd.ensure_trees_transparent`. In the current fixed fixture it admits a
known opaque-to-transparent transition once, refuses repeats and unknown state,
and permits proactive pre-action use as well as uncertain-effect recovery. This
is schema evidence only. A general provider still needs view-state detection,
and a fresh model allocation must test whether proactive transparency improves
correctness enough to justify its cost.

## Pre-action transparency and sign semantics

Allocation v5 applies the tracked opaque-to-transparent transition before the
first planner observation. It takes428.854ms, adds no model boundary and reaches
a rejected verify in7 turns/115,045 input tokens, versus v4's12/198,746. B-to-C
is correct, but A-to-B again occupies tiles912..915 one row above the target.

Allocation v6 changes only the planner instruction to reflect the official
OpenTTD Sign manual: sign boxes annotate map squares, so construction should
target the underlying tile surface. It exposes no calibrated coordinates. Astra
makes12 action proposals and uses199,613 input tokens without verify or safe
stop. At the limit the driver raises before reading the supervisor abort, so no
formal finish evaluation is emitted. All52 exact frames,50 durable calls, typed
proposals and the traceback are retained; the run was not retried. A later audit
of263 continuous source-pinned observer records proves that A-to-B tiles977..979
were built and stable for the final172 records while B-to-C remained empty. The
model repeats the identical A-to-B drag on turns5,9,11 and never attempts B-to-C.
The posthoc artifact/effect audits pass on Windows and WSL. See
`OPENTTD_EFFECT_POSTHOC_V1.md`.

Driver v5 repairs the exposed limit handshake without modifying frozen v4. A
zero-model/zero-pointer live probe sends12 observe-only proposals, waits for the
supervisor stop and records an independent `bounded_turn_limit` outcome after50
durable calls. Release, task/save state and exit0 pass Windows/WSL audit.

Two zero-model Ctrl+1 probes change custom sign presentation without task-state
mutation on this L fixture and the held-out seed991002 straight geometry. The
raw full-frame deltas include simulation progress, so they do not isolate sign
pixels or establish better model grounding. The next comparison needs matched
dynamic state before any model-facing promotion.
