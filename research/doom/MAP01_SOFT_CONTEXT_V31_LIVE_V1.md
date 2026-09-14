# First live typed soft-context transfer

The first and only preregistered v31 allocation runs Luna-low for at most eight
decisions from the distinct `map01-threat-contact-v2` fixture. It is retained as
`RETAINED_TYPED_SOFT_CONTEXT_TRANSFER_PASS`.

## Exposure

All247 exact observations yield health with zero unknown values. The exact
trajectory is97→91→85→79→75→72→71→64→58. Manual review confirms a visible enemy
in every decision frame; decision-source health is97,91,91,85,79,75,71,64 and
ammo is48,48,47,47,46,45,45,45.

Four consecutive control intervals expose the transfer path:

| source→next decision | event bytes | summary bytes | event→next model start |
|---|---:|---:|---:|
| 2→3 | 1,313 | 240 | 3,201.762 ms |
| 3→4 | 1,315 | 241 | 4,721.453 ms |
| 4→5 | 1,314 | 241 | 1,636.701 ms |
| 5→6 | 1,315 | 241 | 3,186.251 ms |

For every exposure, the preceding retained soft event, locally regenerated
summary, next decision record, and exact compact JSON in the saved prompt match.
Each summary explicitly grants no input authority. The transfer uses the same
eight temporal sheets and eight planner turns already required for the eight
decisions, so it adds zero captures, images, model turns, resumptions, or
mid-turn boundaries. Decisions3–5 complete after receiving the history;
decision6 receives it and is later hard-interrupted. The run contains five soft
transitions and three hard invalidations.

This proves delivery and compression mechanics. It does not prove that the
model used the summary causally: current checked health and image evidence are
also present, and there is no matched no-summary arm on this state. The byte
reduction is not an endpoint-token saving; the summary adds a small amount of
text to a prompt that previously omitted this information.

## Authority, timing, and usage

Thirteen programs are accepted and all thirteen end in verified empty key and
button release: eight covers are cancelled and five plans complete. Six planner
turns complete and two are interrupted. Five completed actions are admitted;
the other three answers are discarded. The run remains alive and unfinished
after51.136665049 control seconds and45.555765625 model-wall seconds, with zero
kills, deaths, or exit.

All eight turns emit usage, including the two interrupted turns. Final cumulative
usage is66,366 tokens:65,080 input,37,248 cached input,1,286 output and487
reasoning output. This closes the interrupted-usage missingness seen in the v30
allocation for this run only; it does not establish that future endpoint traces
will always deliver the same notifications.

For the five admitted plans, acceptance-to-first exact post-input capture is
51.203–71.610 ms with median62.594 ms. This is local feedback availability, not
semantic usefulness. The existing viewport-effect classifier reaches its final
sample in151.191–662.189 ms with median415.972 ms; four first commands classify
visible change and one classifies no visible effect. Semantic task completion is
not observed.

Median model-image-capture to plan acceptance is6,994.578 ms and median model
wait is6,572.037 ms. The freshest continuously collected local observation is
only123.288 ms old at plan acceptance, but that frame was not presented to the
model. This distinction identifies the next latency/correctness question: local
feedback is fast, while high-level action is based on an image roughly seven
seconds older unless typed local policy evidence invalidates it. The run emits
22 controller commands,13 Executor acceptances and247 observations; five are
admitted plan programs. Total control time minus summed model time is5.581 s,
which includes plan execution and setup rather than pure framework overhead.

## Newly exposed terminal/invalidation race

Decision0's strict initial floor hard-invalidates at health91 just as the planner
answer becomes terminal. The planner reports completed and answer-eligible, and
the interrupt returns `already_terminal`. The controller nevertheless marks the
model action discarded, admits no plan, cancels the cover and verifies release.
The safety outcome is correct, but the evidence exposes two separate concepts:
planner protocol eligibility and controller final action admission.

The next construction should make final admission a typed receipt with explicit
precedence. A hard event observed before action admission must win even when the
planner has already completed; the receipt should record planner terminal time,
invalidation evaluation time, controller admission decision, reason, and whether
any input was admitted. Model-free race-order tests should cover hard-before-
terminal, terminal-before-hard-before-admission, and admission-before-later-hard.
Do this before a longer MAP01 clear attempt.

V31 runs on a different fixture and for eight decisions, while v30 used six.
Their completion, latency and token figures are descriptive and not a matched
causal comparison. There is no reliability, generality, human-tempo, gameplay,
token-efficiency, Product Hunt completion, or MAP01-clear claim.
