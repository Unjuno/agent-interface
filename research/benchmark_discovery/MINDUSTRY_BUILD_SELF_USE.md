# Mindustry construction through the shared pointer backend

One actual assistant visual episode built six eastward conveyors between the
fixture's copper source and the core. Independent post-control evaluation passes
the declared placement, 112-tile guard and resource-delivery contract. This adds
a construction/transport example to the OpenTTD and desktop pointer evidence;
it is a known development task, not formal benchmark adoption or a speedup claim.

## What was actually controlled

The new setup mod clears the same small floor patch and places only the source.
It resumes the saved world until a live player unit exists, then pauses before
the initial observation. The initial independent snapshot confirms live unit,
zero build plans, 200 copper and empty target tiles. The mod does not author any
conveyors. All route placement uses ordinary clicks/drags through unchanged
`session_v9`/`executor_v3`, the candidate used by the earlier OpenTTD pilot.

The assistant inspected images, selected a conveyor, dragged across the six
visually identified ground tiles, resumed to build and transport, then paused.
Two actual decision errors are retained:

1. The first click selected **Titanium Conveyor**, which requires unavailable
   lead/titanium. Image 003 exposed the wrong selection; a new click selected the
   basic Conveyor, confirmed in image 006 before any construction attempt.
2. After the first drag, pressing **Q** removed the pending construction route.
   Images 007 and 009 show the before/after difference. The assistant restored
   the plan with another drag and resumed without Q. This was a semantic input
   mistake, not a rejected input or a backend crash.

Image 018 shows the completed route, copper=275 and `Paused`. The first successful
route was not silently substituted for the full episode: both mistakes and all
five admitted programs remain in [raw events](results/mindustry-build-self-use-01/events.jsonl).

## Separate construction and delivery accounting

`finish` first closes the executor and releases inputs. A file signal then starts
the declared evaluation phase. The evaluator requires a paused live unit with
zero pending build plans; otherwise it returns UNKNOWN without starting a window.
It snapshots the post-control state, advances the engine with no controller input
for at least 600 ticks, pauses, and captures the final state. Engine pause/resume
in this evaluation phase is fixture administration, not an assistant GUI action.

| Measurement | Result |
|---|---:|
| Copper at episode start | 200 |
| Copper at control closure | 275 |
| Copper after separate delivery window | 323 |
| Delivery during that window | **48** |
| Measured delivery window | 601.438 game ticks |
| Wrong target / collateral tiles | 0 / 0 |
| Guard projection | 112 tiles |

The net increase before control closure includes both construction expenditure
and transport while playing. It is not a build-cost measurement. The final 48
is a separate post-control inventory delta, with identical before/after guard
layout and no pending build plans at its start. Neither figure is a full causal
attribution against alternative resource sources in arbitrary gameplay.

## Audit and timing

[Audit](results/mindustry-build-self-use-01/audit.json) verifies measured source
hashes, replays the independent score, decodes 18 exact AIT observations against
their PNGs, checks all five completed program releases and confirms cleanup.
No inputs/admissions occur after the recorded finish command. Six offline score
controls cover zero delivery, pending builds, an unpaused baseline, a short
window, changed layout and negative initial-to-final net with positive separate
delivery. The last control is synthetic accounting evidence, not another GUI run.

Initial capture to final input-program terminal is **145.184 seconds**; to the
emitted independent evaluation it is **175.052 seconds**. Finish-to-evaluation
is 10.137 seconds, predominantly the declared no-input simulation interval.
Inter-program terminal-to-admission gaps are 25.723, 24.399, 44.803 and 18.745
seconds. These include model/tool/visual-review interaction and are not isolated
model generation times. Only same-Python-process timestamp differences are used.
Actual model input tokens, cost and model receipt endpoints remain missing.

This is plainly not evidence of human-like operating tempo. Wrong selection,
incorrect cancellation semantics and long decision boundaries remain observed
costs despite passing the final task. A matched comparison should preserve those
costs rather than timing only the successful drag or hiding recovery programs.

## Reproduce and limits

Use the existing Linux/X11 assets and a new output directory:

```sh
python3 -u research/benchmark_discovery/mindustry_build_interactive_v1.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/mindustry-build-rerun
python3 research/benchmark_discovery/audit_mindustry_build_v1.py
```

The audit targets the archived cohort. The interactive protocol is the prior
bounded stdin `clock`/`submit`/`cancel`/`finish` interface. Read actual images and
use a fresh runtime lease; do not replay historical deadlines. The build-plan
readiness check follows the pinned release's
[BuilderComp queue](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/entities/comp/BuilderComp.java).

The new split-baseline score is local research code over trusted fixture JSON,
not a general hostile-input schema validator. Its actual samples are audited for
finite ticks and integer copper. Guard coverage is local and final-state based;
temporary collateral edits, global effects, all inventories, alternate resource
acquisition and full trajectory determinism are not covered. Source hashes cover
listed inputs, not an environment lockfile. The inherited ancillary Java/audio
errors remain archived. Failure cleanup still inherits the readiness harness's
limited diagnostic-copy path; this successful cohort has all three snapshots.

Next comparison should consolidate the currently fragmented caller/runtime
candidates and test this construction domain alongside the existing desktop and
OpenTTD cases. The new episode is additional evidence, not an automatic revision
of the scoped historical Evolution Ledger or satisfaction of Research Freeze.
