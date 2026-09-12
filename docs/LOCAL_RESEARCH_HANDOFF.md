# Local research handoff — 2026-09-13

This is the entry point for discussion in another chat. The user has authorized
direct updates to `main` when validated progress is ready. Keep successes,
failures, reproducible code and remaining limitations together in each update.

## Objective

Let the assistant itself operate a changing screen at an ordinary human-like
tempo. Optimize the full observation–decision–action loop, including unnecessary
model/tool boundaries, waiting, input/observation representation and actual token
cost. Preserve task correctness and information needed for decisions. Human-like
performance, real token savings and production readiness are not established.

DOOM is a later real-time evaluation and Product Hunt demonstration milestone:
the game must continue at normal speed while the assistant reasons. It does not
replace desktop task correctness. See [roadmap](../ROADMAP.md).

## Evidence ready for discussion

| Track | Verified result | Limit |
|---|---|---|
| [A1 exact unchanged observation](../research/observation_gating/REPORT.md) | 192 fresh real-app episodes, 96/96 success per arm, 1,446 exact frames; 17.15% same-trace image reduction | Scripted controller, zero model calls; local speedup unproven |
| [A2 exact tile transport](../research/observation_tiles/REPORT.md) | 64 fresh episodes, 32/32 success per arm, 553 exact frames; 70.73% same-trace serialized-byte reduction | Full images restored before viewing; not token savings; local speedup unproven |
| [PNG artifact preparation](../research/observation_tiles/IMAGE_ARTIFACT.md) | Two archived-trace validation replays: reuse saves 10.81% / 16.59% preparation time; level 1 adds 15.89% / 16.03% time reduction with larger PNGs | Offline component timings, not new GUI trials or model latency |
| Actual assistant use | Calc, Inkscape and two XTerm sessions completed by inspecting reconstructed screenshots and choosing actions | Exploratory demonstrations, not a randomized agent comparison |

The A1 and A2 percentages refer to different representations/controllers and
must not be multiplied into a cumulative token or speed claim. Raw failed
freezes are retained alongside successful ones. A2 revision 1 stopped at an
Inkscape baseline drag failure; revision 2 added observations during a planned
segmented gesture in both arms. It does not prove adaptive motor control.

## Most important finding for the next iteration

In the latest assistant-operated XTerm session, local action-to-image-ready time
was approximately 41–56 ms, but two command receipt timestamps were about
10.22 seconds apart. That interval includes inspection, reasoning and tool
boundaries. Further PNG optimization alone will not meet the actual objective.

The new [live-control prototype](../research/live_control/README.md) implements
a separate command reader and GUI worker, early feedback, finite held inputs,
cancellation and verified key release. Six fresh XTerm/Calc functional probes
passed with 54 exact frames; local cancel-to-release times were 0.50–20.79 ms.
These are scripted development probes, not model latency or speedup evidence.
The older `dogfood.py` remains sequential; the new entry point is
`research/live_control/session.py`.

Actual assistant use exposed a different failure: across a context handoff,
cancel arrived about 176.20 seconds after a five-second program had completed,
so its trailing test text ran. The assistant inspected the screen, cleared the
line and recovered successfully, with independent output verification. Preserve
this negative result. Explicit intent expiry, stale-state/focus guards and
guarded local progress remain open; finite duration is not an execution lease.

The [revision 2 follow-up](../research/live_control/DECISION_BOUNDARY.md) adds a
`decide` step that terminates with verified release and discards the tail, plus
rejection of old observation references. In one actual assistant XTerm trial,
the next valid request arrived 10.998 seconds later; the tail stayed stopped
and the fresh task submission succeeded. All 12 frames audited exactly.
This does not detect external screen changes after observation or solve planner
waiting. Avoid requiring a new decision after every low-level action.

The [moving-screen visual tracking study](../research/visual_tracking/README.md)
now tests a pixel-driven local motor method on a continuously moving X11 target.
All 12 frozen six-second episodes completed. At 250 ms decision cadence, mean
error was 39.52 px versus 20.04 px with nominal 50 ms local updates; at 1000 ms,
242.31 versus 20.26 px. This is simulated decision cadence with a fresh image
per update, not in-flight inference delay or model overlap. The assistant also
inspected the start screen and invoked a six-second local method successfully.
Next integrate bounded visual feedback methods into asynchronous execution;
the current tracking invocation itself does not stream planner feedback.

The [async integration follow-up](../research/visual_tracking/ASYNC_INTEGRATION.md)
now connects tracking to the executor and exact observation transport. In two
actual assistant sessions, tracking continued between tool calls and accepted
live cancellation with verified release (35.68/49.84 ms server-local latency).
All 443 recorded frames independently reconstructed exactly. Full streaming
flooded tool output, so a second entry point retains all local events while
returning initial/step feedback, critical control notifications and a polled
latest image. Same-trace replay reduced JSON presentation bytes from 166,673 to
3,304; this is lossy presentation selection, not image-token savings. The latest
image can omit intermediate events. General event escalation and real target
loss/focus drift still require validation.

The [event-retention study](../research/visual_tracking/EVENT_RETENTION.md) now
tests known yellow warnings and target loss in the real private X11 fixture.
Six fresh functional cases passed, with 191 exact frames; one assistant trial
added 21 exact frames. Detected signals retain their evidence image even after
a clear newer observation, block new input until acknowledgement, and stop the
method with verified release. These color-specific detectors do not establish
generic critical-event recall; focus drift and short/unrecognized events remain
open. Next transfer work should start the planned DOOM environment rather than
continue optimizing this simple arena indefinitely.

The [first DOOM-engine transfer](../research/doom/README.md) is now implemented.
The assistant operated ViZDoom 1.3.0's basic room with bundled Freedoom assets
through X11 screenshots and OS keys. Two development runs reached the finish
screen with independent post-control finished/alive confirmation. A revised
clock probe recorded 71 tics over about 2.028 seconds with no advance calls
during the idle interval. Cached API time, case-sensitive window lookup and
ineffective command-line key bindings were discovered and retained; use
`research/doom/session_v4.py`, which supplies an explicit ini. This is a basic
integration, not full DOOM skill, human-speed play or a finished launch demo.

The next controlled evaluation must measure the actual agent loop, completion
quality and measured token use, not replace those with bytes or local timers.
No LLM API/token-metered comparison or comparable human baseline has run here.

## Updated design priorities from the user's candidate report

The [candidate architecture review](CANDIDATE_ARCHITECTURE_REVIEW.md) treats the
new report as design material, not a rewrite instruction. Next priority is an
isolated action-validity/expiry experiment with interaction timing, followed by
observable focus/window validity and an explicit retained-subscription contract.
DOOM remains a transfer environment. Do not substitute basic-room completion
for reducing planner boundaries or for practical GUI correctness. Candidate
future states, leases and semantic versions are not implemented by this note.

## Cooperative expiry experiment

The first [cooperative expiry experiment](../research/live_control/LEASE.md)
now exists. An absolute runtime-clock deadline is checked at admission, during
held input and before key-down. Two fresh paired XTerm cases stop the tail on
expiry and complete via a new intent, while duration-only proceeds beyond the
comparison deadline. Latest release overshoot was 0.929/0.940 ms, not a bound.
Assistant use verified stale-request rejection and fresh completion. A mocked
slow logger exposed late input in revision 3; revision 4 moves logging after
the input call. Blocking can still delay release. Planner/model timestamps,
hard watchdogs and semantic-version guards remain open.

## Input release during worker stalls

The [input-owner experiment](../research/live_control/INPUT_OWNER.md) exposes
and addresses a local failure: 500 ms logging/capture stalls kept the cooperative
backend's key held until roughly 302–372 ms after a 200 ms lease expired in the
fresh paired comparison. A dedicated input thread with its own X11 connection
reduced first-sampled-up delay to 1.2–2.3 ms in four candidate episodes, while
terminal notification remained delayed by the stalled worker. These are local
development measurements, not hard deadline bounds or planner speed results.

Both arms stopped the tail. Twelve retained episodes, six exact frames and
eight tests passed the relevant checks. New real-X11 tests cover independent
cancellation and stale-cleanup ownership. `session_v5.py` is currently a backend
used by the probe, not an interactive entry point or DOOM integration. Ordinary
task completion, robust connection failure handling and actual assistant use of
this backend are the next integration checks. Existing research startup warnings
and temporary-directory cleanup limitations are documented in the report.

## Interactive input-owner follow-up

The [self-use integration](../research/live_control/OWNER_SELF_USE.md) now provides
`interactive_v6.py` with explicit owner lifecycle and task instructions. Actual
assistant use passed XTerm, failed one Calc task by choosing B1 instead of A2,
then passed a new Calc task after the destination was made explicit. The failure
and learning effect are retained; this is not a randomized message comparison.
Eighteen frames and all three saved outcomes were audited. All six programs and
three owner shutdowns verified input release. Local acceptance-to-first-image
timing was 93.5–165.8 ms, not model latency or a performance comparison.

Calc also exposed image/window-context skew around dialog dismissal. Separate
timestamps already exist, but there is no guard for that skew yet. The final
trial requested a fresh observation before ending; saved workbook contents
independently verified success. Focus validity, blocking notifications and
matched planner measurement remain the next work.

## Focus-binding experiment

The [focus experiment](../research/live_control/FOCUS.md) adds before/after
observation focus samples and checks the observed X11 input-focus ID at key-down.
In eight controlled probes, both baseline focus-transfer cases sent a letter to
the other window; both guarded cases stopped without input. Four unchanged-focus
cases completed. Fourteen frames audited exactly. A held-input test verifies
release and persistent invalidation after focus returns. Actual assistant use
also completed XTerm with three exact frames and independently correct saved text.

This is not atomic wrong-target prevention: check/injection races and missed
away-and-back changes remain. `interactive_v7.py` is experimental, and mismatched
capture-time focus samples currently prevent even observe-only recovery. The
next iteration must separate recovery observation from input authorization and
test legitimate modal transitions before adopting this as the default.

## Parallel control-codec discussion (existing branch)

A remote [control-codec research branch](https://github.com/Unjuno/agent-interface/tree/research/control-codec-track)
was observed at `6d49811` during this publication review. It contains control
representation and design-thesis work. It is not merged or validated by this
publication. Keep executable semantics, lossless representation compression and
elimination of unnecessary decisions/boundaries distinct when discussing it.

## Reproduction and provenance

- Begin with [A1 usage](../research/observation_gating/README.md),
  [A2 usage](../research/observation_tiles/README.md) and their frozen protocols.
- Real applications ran in private Xvfb/Openbox sessions under Ubuntu/WSL2,
  using a Chromium-family Chrome for Testing binary, Calc, Inkscape and XTerm.
- Raw manifests contain historical machine paths/timestamps. They are evidence,
  not portable launch configuration; choose new output paths for new trials.
- `.gitattributes` preserves frozen research bytes across checkouts. The shared
  v1 Python source retains its measured CRLF bytes; invoke it with `python3`.
- Research source, packet/image evidence and negative runs are included. Generated
  caches/environments are excluded. No runnable release or Product Hunt launch
  is being published by this update.

For status claims, use [RESEARCH.md](../RESEARCH.md) and the primary reports, not
an unchecked roadmap box or an isolated successful screenshot.
