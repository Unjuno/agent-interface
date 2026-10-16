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

The matched v1 allocation ran once and is retained failed. All four frame arms
passed. All four path arms preserved identical candidate/program, false-then-true
semantics, independent final selection, two exchanges, completed two-step
terminal and empty release, but missed the common200ms first-feedback limit at
216.580–222.920ms. Thus aggregate `all_arms_pass` failed even though every
comparison-mechanics audit passed.

Descriptively, path semantic-ready samples were270.925,297.147,276.620 and
284.453ms; frame samples were236.564,233.990,241.897 and242.707ms. Medians were
280.536 versus239.230ms, a41.306ms advantage and0.8528 ratio, satisfying the
frozen aggregate comparison. These numbers cannot promote the mechanism because
the allocation failed its predeclared baseline health bound.

Ninety-nine files/3,129,166 bytes before retention receipt pass independent
Windows/WSL failure audits. The failure class is
`baseline_first_feedback_bound_incompatible_with_comparison`. V2 may separate
candidate and baseline first-feedback health bounds while preserving every
identity, correctness, release, exchange and aggregate threshold. V1 must not be
rerun or reclassified.

Matched v2 changes only the incompatible health bound. Frame first feedback
remains limited to200ms; the path baseline receives a separate260ms ceiling,
above v1's observed216.580–222.920ms range but below its400ms semantic-ready
ceiling. The≥25ms median advantage, per-mode semantic-ready limits, same
candidate/program, false-then-true semantics, two exchanges, independent score,
exact reconciliation and empty release remain unchanged.

Seed202 provides eight new sessions in the same balanced order. One allocation/
no retry/model/cancel,40 source hashes and absent output are frozen. WSL's12
focused tests pass; Windows passes11 with the expected Unix-socket skip. Freeze
verification passes on both. Commit, run exactly once, audit and retain any
outcome; v1 remains formally failed.

Matched v2 ran exactly once and passed. Path semantic-ready samples were316.836,
275.926,283.566 and291.948ms; frame samples were237.654,234.144,259.626 and
238.422ms. The medians are287.757ms versus238.038ms, a49.718ms reduction and
0.8272 ratio for client-visible admission-to-useful-semantics under the frozen
same-seed comparison.

All eight arms used the same target candidate and canonical click+observe program,
retained first false then useful true in exactly two client exchanges, passed an
independent path score, completed two steps and released to empty input. All four
frame arms stayed within probe bounds and reconciled their exact-frame results to
the ordinary PNG artifacts. Mode-specific first-feedback health bounds pass.

Ninety-nine files/3,130,105 bytes before retention receipt pass independent
Windows/WSL audits. This is causal evidence for a49.718ms median reduction in one
scripted Inkscape semantic-feedback path. It does not establish model reasoning,
token reduction, cross-domain performance or human-tempo operation. The next
promotion test should transfer the same no-authority probe contract to a distinct
GUI predicate or dynamic domain without reusing Inkscape selection semantics.

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

V3 ran once and is retained failed at report construction. Binding readiness was
READY; two pointer admissions, two exact observations, a completed two-step
terminal and empty release all occurred. But the runner indexed `accepted.steps`
as a list although the Executor contract stores integer count2 plus canonical
`program_sha256`, raising TypeError before report serialization.

Posthoc scoring also shows the first observation remained unselected and only the
second observation displayed selection handles. Thus first feedback was not the
first useful feedback. Live scorer-completion clock was lost and cannot be
reconstructed. Eighteen files/496,823 bytes before receipt pass Windows/WSL
failure audits. V4 must bind SHA/count correctly and consume observations until
semantic success or terminal, retaining both feedback clocks.

V4 is frozen with that evidence repair. It checks accepted step count2 and the
canonical SHA-256 of the exact click+observe program. Every new exact observation
is scored in event order with detection and completion clocks. The first feedback
remains separately retained even when semantically false; consumption stops at
the first selection success or terminal.

Seed205 keeps coherent binding, neutral fault, scorer v2 and600/200/300ms limits.
One run/no retry/model/cancel,37 hashes and absent output verify;12 focused tests
pass Windows/WSL. Run once and retain any result; v3 remains failed.

V4 ran exactly once and passed the frozen allocation and independent retained
audit. Runtime release reached the early client at3.115ms after focus request,
while the terminal client returned at83.150ms, an80.035ms wait advantage. Early
preparation produced fresh useful readiness at105.835ms versus133.249ms for the
terminal-first arm, a27.413ms advantage. The newly bound selection was accepted
at252.015ms after focus request, completed two steps and ended with verified
empty input.

The first feedback frame was captured89.364ms after acceptance and received at
157.062ms, but correctly scored unselected. The first useful frame was captured
at162.540ms; semantic scoring completed at279.520ms after acceptance, or531.536ms
after focus request. The execution terminal completed37.876ms before semantic
scoring did. This separates frame availability, recognized semantic completion
and program lifecycle closure instead of treating the first observation or the
terminal as task completion.

Eighteen files/540,548 bytes before retention receipt pass independent
Windows/WSL audits. The result covers one private-Xvfb Inkscape fixture with no
model, retry or cancellation. It establishes neither token reduction, general
speedup nor human-tempo operation. The next comparison should reduce recognition
time with an incremental or in-memory scorer while reconciling its result to the
exact retained frame.

## Frozen exact-frame probe comparison

The first recognition refinement moves the same selection predicate onto the
already reconstructed exact RGB frame. It computes red support and four handle
zones with bounded NumPy slices, emits a dimensions-and-pixels frame digest and
grants no input authority. A separate reconciliation reopens the durable PNG and
requires the same exact-frame digest, retaining artifact SHA separately.

The offline seed-free allocation compares the old path/Pillow pixel-loop scorer
with the frame probe on retained v4 `004.png` (first feedback, false) and
`005.png` (first useful feedback, true). Sixteen ABBA cycles produce64 samples
per mode. Every semantic field must match, both artifacts must reconcile, frame
median must be at most5ms and at most25% of path median. One run/no retry/model,
exact source hashes and absent output are frozen. Six equivalence tests and
freeze verification pass on Windows/WSL. Run once under WSL, audit and retain the
first outcome. This isolates scorer compute only; it cannot claim a live latency
gain until integrated before artifact publication.

The allocation ran once and passed. Across64 samples per mode, the old path
scorer median was34.696ms and p95 was42.365ms. The exact-frame probe median was
2.320ms and p95 was2.630ms: a32.376ms median compute advantage and a0.0669 ratio.
The false/true result pair and every retained semantic field matched, and both
frame digests reconciled to their exact PNG artifacts.

Three files/197,729 bytes before retention receipt pass independent Windows/WSL
audits. This supports replacing the scorer's PNG-open/Python-pixel-loop compute
once the exact frame already exists. It does not measure event detection, PNG
publication or integrated live completion. The next live allocation must run the
probe on the reconstructed frame before artifact publication, retain its result,
then reconcile it to the published PNG without using the probe as input authority.

## Frozen live pre-artifact semantic probe

V5 versions the live observation path instead of changing any retained source.
A backend-independent registry copies one no-authority predicate for the new
action. After lossless wire reconstruction, the versioned backend scores the
exact RGB frame, emits an action-scoped `semantic_probe`, then prepares the PNG.
It subsequently emits a digest reconciliation and the ordinary exact observation.
The provisional event grants no input authority and cannot substitute for later
artifact evidence.

The event cursor and Unix socket are separately versioned to admit
`semantic_probe|terminal` under the same bounded action-id rules. A client read
is registered before selection submission, consumes the first false probe, then
resumes from its cursor to the first true probe. The click+observe program,
coherent admission, exact terminal and empty release remain unchanged.

Seed204, one run/no retry/model/cancel,43 source hashes and absent output are
frozen. Both probes must compute within5ms, complete before their PNG-ready clocks
and reconcile exactly. Client bounds are200ms to first feedback and250ms to
semantic success; prior600/300ms internal bounds remain. Twelve focused tests
pass on WSL; eleven pass and the Unix-socket-only test skips on Windows. Freeze
verification passes on both. Commit, run exactly once and retain any outcome.

V5 ran exactly once and passed the frozen allocation and retained audit. The
first false probe computed in3.171ms and reached the scoped client122.424ms after
selection acceptance. The useful probe computed in2.623ms, completed223.959ms
after acceptance and reached the client at224.724ms. Its PNG became ready29.623ms
after probe completion, so the client received the useful semantic result about
28.858ms before the durable PNG was ready. The completed two-step terminal
followed the client result by68.647ms, with verified empty input.

For descriptive context, v4 recognized its useful frame279.520ms after admission
and37.876ms after terminal. V5's useful frame itself arrived later than v4's
(195.293ms versus162.540ms after admission), yet its meaning reached the client
earlier and before terminal. Different seeds prevent a matched causal speedup
claim, but the changed boundary behaved as intended under worse visual-arrival
timing.

Eighteen files/577,889 bytes before retention receipt pass independent Windows/
WSL audits. Both provisional frame scores exactly match the independent path
scorer and reconcile to their durable PNGs. The remaining measured delay is now
mostly capture/context/wire reconstruction before the2–3ms probe, rather than
post-observation pixel scoring. A matched live control should isolate the causal
gain before promoting this boundary beyond the fixture.

## Frozen matched live semantic delivery

The causal comparison uses eight fresh private-Xvfb Inkscape sessions with the
same seed203 task, candidate and exact click+observe program. The fixed
path/frame/frame/path/frame/path/path/frame order balances first/last and adjacent
runtime effects. The path client waits for an exact observation and then runs the
existing PNG scorer. The frame client waits for the pre-artifact probe. Both use
the same action-scoped socket, retain first false then useful true feedback in two
exchanges, and preserve normal observations and terminal evidence.

Every arm must independently verify selection, complete two steps and release to
empty input. Frame probes must remain within5ms and reconcile to their PNGs.
Frozen aggregate limits require frame semantic-ready median at most260ms, path
median at most400ms and a frame advantage of at least25ms. Seed203, one eight-arm
allocation/no retry/model/cancel,40 source hashes and absent output are frozen.
Twelve related tests pass on WSL; eleven plus one expected Unix-only skip pass on
Windows. Freeze verification passes on both. Commit, execute exactly once, audit
and retain the first outcome.


## Cross-domain semantic-probe transfer

The typed no-authority registry now supports an exact bounded RGB crop predicate
as well as the Inkscape selection predicate. Historical calibration accepted
four Chromium success frames and rejected unsubmitted and blank controls. The
first frozen live transfer remains formally failed because its checker equated
all generated reconciliations with the smaller set consumed before the client
stopped at success.

A fresh v2 allocation changed only that collection-cardinality rule and passed.
It rejected the blank negative, detected `Submission received`, independently
saved `t000207`, reconciled every exact frame and ended every program released.
Useful feedback arrived286.471ms after submit admission,24.767ms before its PNG
and156.657ms before terminal. Treat this as one Chromium predicate transfer.
Next make the crop target-relative and test surface translation/resize against
existing freshness and target-handle boundaries. See
`CHROMIUM_SEMANTIC_PROBE_TRANSFER_V1.md`.


## Target-relative semantic geometry

The Chromium crop is now stored in `window_content` coordinates and evaluated
against a coherent current surface binding. V1 moved the real surface `[21,28]`
but the executor safely refused before input because its last observation still
described the old geometry. V2 added one passive post-move snapshot and passed:
the relative predicate followed the move, the fixed crop failed on the same
frame, and a later width change refused before crop hashing. Useful feedback was
275.781ms after admission,23.828ms before PNG and134.919ms before terminal. The
next boundary should derive this region from a verified target handle and perform
bounded local repair after resize. See `TARGET_RELATIVE_SEMANTIC_PROBE_V1.md`.


## Target-handle semantic repair

The completion region can now be derived from a verified Save target handle plus
a bounded cached relation. After a live width resize, the old predicate refused
before crop hashing. The same handle's current exact pixels revalidated in
0.091ms and generated a current-geometry predicate in0.145ms, with no frontier
resumption. The repaired task completed and delivered useful semantics in
271.178ms. This relation is calibrated; compare it against same-model
reacquisition before claiming token or latency savings. See
`TARGET_HANDLE_SEMANTIC_REPAIR_V1.md`.


## Matched repair comparison: upstream capacity failure

The first frozen local/model comparison did not reach either repair branch.
After arm1 completed form navigation and token entry, the required initial
Luna-low grounding turn was refused because the model was at capacity. No turn
completed and no usage record, handle, resize, semantic probe or Submit exists.
Cleanup released empty input. The34-file/469,683-byte first outcome passes
independent Windows/WSL failure audits and remains failed without retry. The next
version must type upstream invocation failures and establish an explicit
service-admission/defer boundary before task input. See
`MATCHED_SEMANTIC_REPAIR_V1.md`.


## Typed model-service admission

The retained capacity result now maps to `DEFERRED_UPSTREAM` and then
`TASK_DEFERRED`, with no grounding reference, usage, semantic authority or input
authority. Validated completion alone is task-mutation eligible and still cannot
bypass ordinary Executor admission. Other process failure and invalid exit0
output remain separate blocked states. Seven Windows/WSL replay and negative
controls pass without a new model or GUI call. See
`SEMANTIC_GROUNDING_ADMISSION_V1.md`.


## Matched repair v2: model result outlives source freshness

Capacity-aware v2 reached the actual comparison path. Local arm1 completed with
correct independent output and release. Model arm2 reacquired the correct Save
point after8,262.886ms, but the source frame allowed3,000ms freshness. Exact
handle resolution therefore refused `STALE` before contract or Submit. A
model-free retained-frame control resolves the identical patch fresh and refuses
it after the observed wait. Three calls report28,053 input tokens; no balanced
comparison was computed. The next version must take one passive post-model exact
observation and revalidate the patch there.


## Matched repair v3 passes

One post-model passive exact observation and a source/current patch receipt repair
the v2 freshness failure. All four seed215 sessions save the exact token and
release. Local recovery median109.966ms/input9,351 versus Luna reacquisition
8,115.268ms/input18,702; bounded differences8,005.302ms and9,351 tokens. The two
model arms refresh in75.592/66.802ms and revalidate in0.071/0.066ms. Six calls and
189 files audit cross-platform. This retains a calibrated local-first route, not a
general saving claim; next integrate typed fallback branches in the shared caller.
