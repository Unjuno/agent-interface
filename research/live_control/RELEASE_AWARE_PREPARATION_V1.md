# Release-aware planner preparation v1

The client-wait v2 result exposes a bounded interval after physical input is
verified empty and before the prior program terminal arrives. This contract lets
a planner use that interval to prepare a candidate while preserving the later
terminal as a mandatory reconciliation boundary.

Preparation can begin only after the exact action-scoped, token-bound release has
been ingested. A prepared candidate is copied and deterministically fingerprinted.
It never grants input authority and cannot submit to Executor. After a matching
terminal arrives, the state becomes `PREPARED_REQUIRES_FRESH_ACTION_VALIDITY`;
the existing final-action-admission v2 boundary must still validate current
evidence and bind a fresh Executor acceptance.

Wrong-token or conflicting terminal evidence fails closed. The contract records
how much preparation overlapped the terminal wait without treating that duration
as useful work or a speedup. This is model-free construction. It has not yet run
an actual planner, reduced useful-action latency, or shown a token/task benefit.

## Frozen visual-planner allocation

The first live comparison uses the actual Inkscape fixture rather than an
artificial sleep. Both same-stream arms scan the same initial PNG inside a fixed
ROI, require one solid red rectangle, and prepare its exact bounding box, center
and click candidate. The early arm starts after verified release and separately
waits for terminal; the baseline starts only after terminal delivery. Both then
validate the target against the actual post-release PNG. No prepared candidate
is submitted to Executor.

Seed209, one allocation/no retry/model/cancel,34 source hashes and absent output
are frozen. Bounds require early fresh-validated readiness within200ms, at least
5ms advantage over terminal-first, and terminal-first readiness within300ms.
The exact expected target is bbox[596,373,643,408],1645 red pixels and center
[619,390]. Windows/WSL freeze verification and10 related tests pass. Run once
and retain the first outcome.

The allocation ran once and passed its frozen audit. Release was verified at
17.787ms and the early client returned at26.378ms. Early candidate preparation
completed77.638ms after focus request, before terminal at approximately110.755ms;
terminal-first candidate preparation completed139.137ms. After exact terminal
reconciliation and the same fresh-PNG validation, early useful readiness was
136.273ms versus164.592ms, a28.319ms advantage. Both arms produced the exact
frozen target and no candidate input was admitted.

Twelve files/266,171 bytes before retention receipt pass independent Windows/WSL
audits. This is evidence for one fixture-scoped visual preparation overlap, not
for model planning, executed task progress, token reduction, general speedup or
human-tempo operation. The next test must bind one freshly revalidated prepared
candidate to a new Executor acceptance and independently score its visible effect.

## Frozen prepared-selection allocation

The next distinct seed208 allocation restores the original focus after the
interruption, captures a third exact PNG, and revalidates the early candidate.
It then submits exactly that click followed by one observation under a new
Executor action. An independent scorer requires the same red rectangle and dark
selection handles on all four sides; the pre-click frame must fail this score.

The first feedback observation, scorer completion, completed two-step terminal
and verified empty release are retained. Bounds are500ms fault-to-semantic-score,
200ms admission-to-first-feedback and300ms admission-to-score. One run, no retry,
model or explicit cancel,35 source hashes and absent output are fixed. Twelve
related tests and freeze verification pass on Windows/WSL. Run once and preserve
any outcome.

The allocation ran once and is retained failed. The fault click itself targeted
the red rectangle, so the restored-focus `003.png` already showed four-sided
selection handles before prepared-candidate admission. The later click completed
and produced exact feedback, but Inkscape selection overlays changed the red
support from1645 solid pixels to1439 pixels. The frozen v1 scorer raised
`red target must be one solid rectangle`. Cleanup then cancelled the second
observe step, leaving a one-step cancelled terminal with verified empty release.

This is `selected_precondition_and_strict_overlay_identity_rejection`, not a
passing semantic-completion result. Eighteen files/503,386 bytes before receipt
are retained and audit on Windows/WSL. Do not rerun v1. The next allocation must
place the interruption click on neutral canvas and version the scorer to tolerate
bounded selection overlays while preserving target identity.

V2 freezes that changed condition separately. Its fault click is neutral canvas
[730,500], outside the red target. Selection scorer v2 allows at most1px edge
shift and requires at least80% of source red support, then independently requires
at least10 dark handle pixels on every side. It passes the retained rectangle-
tool and selector overlays and rejects the retained unselected image.

Seed207 keeps the prior500/200/300ms semantic bounds, one run/no retry/model/
cancel and exact execution/release rules. All35 hashes, absent output and12 tests
verify on Windows/WSL. Run once and retain any outcome; v1 remains failed.

V2 also ran once and is retained failed for a different reason. Neutral fault and
unselected target checks passed exactly. The first restored-focus snapshot straddled
window-manager activation: pointer context had no surface before capture and a
valid surface after capture, so its coherent `pointer_binding` was null. Visual
validation alone admitted a doomed program; Executor accepted it, then refused
before pointer input with a zero-step `needs_decision` terminal and empty release.

The client waited only for observation, missed that terminal and spent its full
three-second timeout. Fourteen files/326,224 bytes before receipt pass Windows/WSL
failure audits. V3 must require coherent binding before acceptance and wait for
`observation|terminal`, preserving the neutral fault and scorer v2.

V3 constructs both shared repairs. A no-authority pointer-binding readiness
receipt requires capture-before, capture-after and published binding to contain
the same non-null focus, surface and geometry. After focus restoration the runner
takes at most three passive observations10ms apart and submits nothing until READY.
After acceptance a first-boundary reader resolves observation or terminal, so a
pre-input refusal cannot consume the old three-second observation timeout.

Seed206 retains neutral fault, scorer v2, exact candidate execution and empty
release. Bounds are600ms fault-to-score and200/300ms acceptance-to-feedback/score.
One run/no retry/model/cancel,37 hashes and absent output verify;12 focused tests
pass on Windows/WSL. Commit, run once and retain any result.
