# Normal MAP01 live-control development

This pre-formal series uses the packaged Freedoom 2 MAP01 as an ordinary,
continuously advancing game. It is not a test scenario. The engine runs at 35
tics/second during capture, model inference, and command dispatch. Controller
input uses the shared X11 owner only; pause, save states, action vectors,
automap, object labels and sector labels are prohibited.

The initial stop-inspect-submit controller died. A later controller overlaps
Luna-low inference with bounded cover programs. Three calls totaling 26.764
seconds were fully overlapped and the game was unfinished with the player alive
at the end of 40.903 wall seconds. Constant cover fire exhausted ammunition, so
later revisions replaced it with bounded no-input observation and conditional
fire pulses.

`coast_backend_v1.py` composes a no-input `coast` operation over the existing
pointer and drag-checkpoint backend. The canonical real MAP01 probe observed for
2.096 seconds, produced seven exact frames, admitted zero inputs, and verified
empty key/button state on release. Two earlier prototypes accidentally reused
the existing `session_v9.py` and `session_v10.py` names. Those files were
restored; the prototype sources and supersession records are retained.

A 2x2 temporal sheet packs four recent game windows into roughly the same image
extent as one cropped window. It enabled Luna to identify repeated-wall stalls.
The raw `observation_to_plan_accept_ns` field in that first temporal run is
invalid because it was computed after the plan completed; all eight values are
negative. Later controllers separately record model-image age and the final
observation-to-admission interval.

The model responder initially omitted key meanings, and Luna described firing
while emitting `a`, which is strafe-left. The corrected contract explicitly
states all bindings. A 12-turn corrected run ended unfinished after 158.494
seconds. This is no clear claim.

One persistent-session mechanics probe kept the same Luna thread ID. Its cold
turn used 9,000 input tokens with no cache hit; the resumed turn used 9,629
input tokens, of which 7,936 were cached. Uncached input fell from 9,000 to
1,693, while local runner time fell from 9.605 to 7.806 seconds in that pair.

In live play, 12 fully persistent turns used 149,089 input tokens, including
126,208 cached and 22,881 uncached. The corresponding 12 ephemeral turns used
104,054 input tokens, including 6,912 cached and 97,142 uncached. Persistence
reduced uncached input by 76.446% but increased total model wall time by 17.077%
in these unmatched allocations as history grew. A
four-turn hybrid over 20 decisions used five model sessions and 78,132 uncached
tokens; it ended unfinished after 257.179 seconds. These different-seed runs
show a tradeoff and do not establish a causal latency gain.

The bounded cover duration is ten seconds. Several later model calls exceeded
that limit, so their tail ran with the game advancing but no active program.
The audit reports the actual covered fraction rather than treating every model
interval as fully overlapped.

The scorer now exposes `DEATHCOUNT`, `KILLCOUNT`, and `one_life_map_exit` after
control. A skill-5 calibration reached one terminal death and reported
`death_count=1`. Earlier visual evidence suggesting a restart is insufficient;
death-count persistence through an actual in-session restart remains untested.

No run has exited MAP01. The current dominant control failure is coarse blind
turn duration: model-authored turns around 1.2--1.7 seconds repeatedly
overshoot into another wall. The next candidate should compile semantic motor
commands into short calibrated turns and movement pulses, then compare it with
the raw-duration contract under a fixed protocol.

The first semantic-motor allocation replaces raw keys and durations with ten
named actions and four extents. The local compiler caps turns at 450 ms and
movement at 900 ms. Over 20 decisions it ended unfinished with zero recorded
deaths, one kill, and 181.263 seconds of control time. The raw-duration hybrid
used 257.179 seconds for 20 decisions. Model time was 156.602 versus 168.681
seconds; model-external time was 24.661 versus 88.498 seconds. The scoped total
and model-external reductions are 29.52% and 72.13%. This is a different-seed
exploration result, so it motivates a fixed comparison but does not prove a
causal gameplay improvement. The final health was 7 and the map was not exited.

An extended 30-turn allocation conditionally continued the previous defensive
intent during model inference. It ended unfinished after 289.861 seconds with
zero deaths, zero kills, and 100 health. The trigger rarely activated in this
seed. The run reached a new green-sign/`A` area but spent more than fifteen
decisions oscillating around walls and a doorway. This does not validate the
reflex candidate. It identifies the next missing layer as bounded stagnation
detection and compact topological memory rather than another longer run.

[The first visual-stagnation study](MAP01_STAGNATION_V1.md) tested that next
layer in a same-seed ordered three-arm allocation. Forced recovery and a later
planner-only advisory both changed behavior but failed to exit MAP01 and
increased detected revisits versus the baseline (10 and 18 versus 5). The
advisory added 6,565 total input tokens versus the baseline in this allocation.
Neither candidate is promoted. The result redirects the next iteration toward
per-command visual effect receipts rather than another repeated-view directive.

[Command-effect receipts](MAP01_EFFECT_RECEIPT_V1.md) now reuse observations
already emitted during each hold. A compact projection sends only action names
with no visible effect and adds no executor steps. A 40-decision same-seed pair
remained unfinished in both arms, with 8 baseline versus 9 candidate revisits.
The candidate's first visual feedback median was 47.17 ms, but the next
model-authored plan was admitted 8,682.54 ms after a no-effect observation.
This motivates preplanned local contingencies; no gameplay gain is claimed.
