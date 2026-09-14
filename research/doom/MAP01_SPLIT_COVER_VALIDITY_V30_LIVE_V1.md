# First live split cover-validity result

The first and only preregistered v30 fixed-threat allocation is retained as
`RETAINED_SPLIT_VALIDITY_SOFT_EXPOSURE_PASS`. It tests whether a planner-authored
absolute critical-health floor and a separate bounded-loss allowance can keep an
already admitted local cover running through expected damage while preserving
the existing hard-interrupt path.

## Frozen allocation

- allocation: `map01-split-cover-validity-v30-live-01`
- model: Luna, low reasoning
- decisions: 6
- fixture: real Freedoom MAP01 `map01-threat-contact-v1`
- retries: none
- source hashes: all match the committed preregistration

The run ended alive and unfinished after 36.056789397 control seconds and
31.081937343 model-wall seconds, with zero kills, deaths, or map exit. These
game scores are context for the mechanism result, not evidence of improved play.

## Result

All 154 exact observations yield a HUD health value and none are unknown. Manual
review of the six decision frames confirms health `100, 97, 90, 84, 84, 78`,
ammo `50, 50, 50, 50, 49, 47`, and a visible enemy in every frame.

The first three turns hard-invalidate at health 97, 90, and 84. Each matching
turn is interrupted and its cover releases. Decision 3 then completes and
authors a nonempty cover with critical minimum 64 and maximum loss 10. Decision
4 admits it at source health 84, deriving an effective hard floor of 74.

At exact sequence 73, health 78 is therefore a soft transition. The runtime does
not interrupt the planner or revoke the existing cover. Nine later cover steps
start, including seven real input-hold steps, and the same planner turn completes
6,503.264369 ms after evaluation. This is the first retained live case where a
nonempty local cover absorbs a typed health change and continues useful input
while its matching high-level decision finishes.

Decision 5 begins with an empty cover and effective floor 68. Health 74 and 73
are both soft; the newest event at sequence 137 is retained and the same planner
turn completes. These two events verify coalescing under input-free cover but do
not add motor-continuation evidence.

Across the run there are three hard invalidations, three soft transitions, zero
validity-admission rejections, and three completed turns. All nine accepted
programs end with independently verified empty input release. No dependent plan
is admitted from an interrupted turn.

## Timing and accounting

For the three hard events, capture-to-monitor receipt is 75.738–79.490 ms,
deterministic signal extraction is 14.862–15.759 ms, and outcome evaluation is
0.031–0.036 ms. Evaluation-to-cover-release is 7.720–11.347 ms. These clocks
separate observation delivery, HUD extraction, predicate evaluation, interrupt
dispatch, and release instead of combining them into one latency number.

The persistent planner uses one process and one thread for all six turns, with
three interrupts and three completed-turn usage notifications. The last known
cumulative completed usage is 34,998 tokens: 34,332 input, 27,264 cached input,
666 output, and 260 reasoning output. Usage consumed by interrupted turns is
unattributable with the current endpoint notifications and must not be treated
as zero.

## Interpretation and next test

The descriptive completion counts are v28 1/6, v29 2/6, and v30 3/6. These are
single nondeterministic allocations with different mechanisms, so they do not
establish a causal completion-rate, latency, token, survival, or gameplay gain.
V30 is also slower in total wall time than the comparison needed for any speed
claim.

The mechanism gate itself passes: bounded soft evidence preserved existing
authority, continued nonempty input, and allowed the matching planner turn to
complete; hard evidence retained cancellation, interruption, stale-answer
refusal, and verified release. Preserve this result without rerunning the same
fixture. The next construction should expose the newest typed soft-event summary
to the next planner turn without adding an image or model boundary, then test
the mechanism outside this exact fixed-threat state before attempting a full
MAP01 clear.

The retained directory contains the preregistered artifacts, all 154 exact
observations, program receipts, protocol transcript, manual frame review,
retention manifest, and machine-readable `audit.json`.
