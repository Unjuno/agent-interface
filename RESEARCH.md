# Research index

Agent Interface is being developed by experiment, not by locking an API early. This file is the evidence ledger for the public repository.

## Research question

Can a strong planner control arbitrary GUI applications through a local interface that:

- works on an unknown app immediately,
- reduces model boundaries and repeated observations,
- learns reusable routes from successful use,
- survives UI/environment drift by invalidating only stale layers,
- and preserves correctness as a hard gate?

## Experimental ladder

### Current real-time gate — typed liveness construction passes replay

The first fixed-threat v28 allocation starts from a hash-bound real Freedoom
MAP01 state whose exact initial frame visibly contains an enemy. Five of six
Luna-low turns are naturally invalidated as reviewed health changes from 100 to
73. Every matching turn becomes ineligible, one nonempty stale cover is
cancelled, no discarded plan is admitted or inherited, and all seven admitted
programs verify empty release. One fresh decision completes on the same
app-server thread after the first interrupt. Detection-to-interrupt-send is
0.026–0.324 ms and detection-to-cover-release is 20.435–25.048 ms.

This closes the previously unexposed natural stale-cover safety path and exposes
the next failure: repeated damage can starve high-level replanning. The selected
next question is a typed cover-validity envelope that lets a bounded local layer
absorb explicitly expected observable transitions while hard contract breaches
still revoke authority. See [the retained v28 result](research/doom/MAP01_FIXED_THREAT_V28_LIVE_V1.md)
and [replanning liveness design](research/doom/REPLAN_LIVENESS_V1.md). No
gameplay-quality, survival, token-efficiency, reliability, human-speed, or
MAP01-clear claim follows from this one allocation.

A model-free typed validity construction now replaces directionless HUD pixel
change with hash-bound WAD-glyph health extraction. It reads all70 exact v28
observations with zero unknown signals and matches19 manually reviewed values
across v28 and an independent v23 allocation. A development-only posthoc health
floor preserves the existing policy through87 and81, then hard-invalidates at
79, 17 exact samples and5,240.235886ms after v28's first raw change. This passes
the extraction, fail-closed, one-way-authority and coalescing checks, but does
not run a planner or prove useful progress. The next gate is model-free
controller integration of typed soft preservation and hard cancel/release. See
[the replay report](research/doom/MAP01_COVER_VALIDITY_REPLAY_V1.md).

V29 carries this into schema/controller construction. Each active planner answer
must attach one typed health floor and lease to its next cover. Admission binds
the condition to fresh exact evidence; already-breached or over-wide envelopes
admit no prior cover commands. Soft events remain coalesced, while hard/unknown/
expired evidence uses the inherited planner-interrupt, cover-cancel, verified-
release and stale-answer discard path. The relevant32-test Windows set and15-
test WSL/Linux subset pass. No v29 model/game allocation has run; the20-health
maximum soft-loss cap is a construction bound awaiting a frozen test. See
[the v29 contract](research/doom/MAP01_TYPED_COVER_VALIDITY_V29.md).

The first preregistered v29 live allocation is retained soft-unexposed. All109
exact frames yield health with zero unknowns, four turns hard-invalidate, two
complete, and all eight programs verify empty release. Luna twice authors floor
30. At source health84 this exceeds the frozen maximum20-loss envelope, so the
runtime correctly rejects all three prior cover commands and uses input-free
coast. Soft events remain0; the change from v28's1 completed turn to v29's2
cannot be attributed to the mechanism. The contract must separate absolute
critical health from bounded short-horizon loss and retain monitor-stage clocks.
See [the retained v29 result](research/doom/MAP01_TYPED_COVER_VALIDITY_V29_LIVE_V1.md).

V30 repairs that representation model-free: schema v5 separates absolute
critical health from a statically bounded0–20 short-horizon loss and derives the
effective floor as their maximum against fresh source health. V29's retained
84→78 change is soft under critical30/loss20; v28's93→87→81→79 sequence is
soft/soft/hard under critical30/loss13. These loss values are construction
inputs, not model evidence. Monitor v2 adds receive, extraction-complete and
evaluation clocks. Windows43 and WSL/Linux15 tests pass; no v30 live allocation
had run at the construction freeze. See [the v30 construction](research/doom/MAP01_SPLIT_COVER_VALIDITY_V30.md).

The first and only preregistered v30 allocation now exposes the intended live
soft path. All154 exact observations yield health. A nonempty cover admitted at
health84 derives effective floor74; exact health78 is soft, nine later cover
steps begin, seven hold real input, and the same Luna turn completes. Three hard
events still interrupt matching turns, and all9 programs verify empty release.
Two more soft values occur under empty cover. The 3/6 completed turns beside v29
2/6 and v28 1/6 are descriptive single allocations, not evidence of causal
speed or gameplay gain. Next pass the newest typed soft summary into the next
planner prompt without another image/model boundary, then test transfer outside
the fixed fixture. See [the retained v30 live result](research/doom/MAP01_SPLIT_COVER_VALIDITY_V30_LIVE_V1.md).

V31 now implements that transfer model-free. It validates the immediately
preceding typed soft event, strips glyph/binding/timestamp detail, and compresses
the retained v30 decision4 event from1,312 compact-JSON bytes to240. The bounded
summary is added to the next planner turn that already occurs, with zero extra
image, call, resumption, mid-turn boundary, or input authority. Missing evidence
is null; inconsistent or authority-granting evidence fails closed. Nine tests
pass on Windows and WSL/Linux. No v31 live allocation exists; the next frozen
test should use a different reproducible threat state or bounded normal-MAP01
continuation. See [the v31 construction](research/doom/MAP01_SOFT_EVENT_CONTEXT_V31.md).

The first transfer fixture is now frozen before execution. Session v8 can load
the hash-bound v1 parent and save one setup-only child while retaining parent
hash/tic provenance; v7 and frozen results stay untouched. One model-free X11
continuation uses strafe-left, retreat-fire, strafe-right and750ms coast. The
first outcome must be retained without retry and must show a different tic/frame,
exact health, visible threat, verified releases and fresh-process reload before
promotion. Linux14 construction tests pass. No planner or performance evidence
exists yet. See [the v2 fixture plan](research/doom/MAP01_THREAT_FIXTURE_V2_PLAN.md).

That one frozen continuation is now promoted as `map01-threat-contact-v2`.
Model-free X11 setup advances parent tic1263 to1366 with two verified releases
and zero model calls; its source frame hash differs. Direct and exact-HUD review
shows a visible enemy at source health100/ammo48. A fresh process restores tic
1366 and its first continuously advancing frame still shows the enemy at exact
health97/ammo48. The100→97 load-to-capture change remains explicit. This is a
different reproducible state for one v31 transfer allocation, not performance
evidence. See [the retained v2 fixture](research/doom/MAP01_THREAT_FIXTURE_V2.md).

### Integrated token-efficiency comparison selected

[Integrated efficiency plan v1](research/live_control/INTEGRATED_EFFICIENCY_PLAN_V1.md)
closes the preceding isolated-mechanics block and selects one finite end-to-end
comparison for Issue #57. A real batched plain visual program, the current
ephemeral optimized path and a persistent integrated path receive the same six
cold/warm/layout-change/repair tasks.  Correctness, stale input, complete model
usage, planner generations, feedback latency and observed break-even are frozen as
separate measures. The retained allocation scores 6/6 exact in all three arms.
At task 6, cumulative input is 63,128 plain, 63,779 ephemeral, and 26,563
persistent; generation counts are 7/7/3 and measured break-even is task 2.
Six-task elapsed time is 56.412/73.238/44.131 seconds. This is one sequential
sequence rather than a general efficiency rate. The real-time MAP01 gate remains
separate in the Domain Coverage Matrix.

The selected fixture now passes a six-task persistent engineering sequence with
human-inspected points: exact-once6/6, four mints, A/B reuse, task-4 old-handle
`MISSING`, zero old-target input, 12 intended button downs and41/41 releases.
Five retained allocations expose point-frame, nullable-refusal, patch-size and
pointer-accounting failures before that pass.  With the earlier URL and global
call-ID defects, [the integration discovery ledger](research/live_control/integrated_efficiency_discoveries_v1.json)
classifies two interface mismatches and four benchmark/setup/accounting defects.
The composed trace validator requires their provenance and forces HOLD for an
allocation-invalidating formal discovery.  These zero-model engineering runs do
not establish the pending token/latency comparison.

A new common client then completes a fresh human-point mechanics pass across all
three arms,18/18 exact tasks.  Plain, ephemeral and persistent use0/12/4 mints,
18/48/41 programs and36/96/82 durable calls with36 total intended button downs
and verified release at every terminal.  The first run's invalid task-derived
alias is retained and added as a third interface mismatch.  The genuine batched
plain arm now has a strict two-point-only model schema, while B/C retain the
compiled method schema; a shared Luna-low adapter supports both.  No fresh model
call or efficiency measurement is included in this engineering pass.

### Compiled GUI interface live mechanics and typed composition

A preregistered Chromium sequence preserves three failed allocations before the
mechanics pass: batched handle minting, a visually-flat field patch and a
read-check status mismatch.  V4 then completes the positive two-action method and
stops the changed page before Submit, while exposing that caller v1 turns nested
`unknown_state` into generic `failed`.  Caller v2 adds a strict bounded safe-yield
contract.  Fresh seed991025 v5 independently submits `t991025`; the changed case
returns `unknown_state`, `completed_actions: 1` and `confirmed_partial` across the
outer boundary.  Positive feedback arrives in773.005ms and568.488ms, and semantic
completion in1.855s after the first action.  Two calls report18,792 input tokens.
Windows/WSL audits and manual frame review pass.  This advances to matched
efficiency comparison without a speed, token, rate or human-tempo claim.  See
[compiled GUI interface live v5](research/live_control/COMPILED_GUI_INTERFACE_LIVE_V5.md)
and [adaptive caller v2](research/live_control/ADAPTIVE_ACQUISITION_CALLER_V2.md).


### Model-proposed active semantic evidence

One held-out OpenTTD toolbar target now tests a single Luna-low planner on both
coarse proposal and semantic evidence selection. The first preregistered pair is
retained failed: its self-reported unambiguous three-point set omits company
finances and the independent oracle remains false. V2 detects30 repeated toolbar
slots from source pixels and probes the five-slot neighborhood around the coarse
model anchor in two runtime-bounded batches. A corrupted point/receipt association
refuses before the second model call and target input. Stable selects receipt5 at
`[485,51]`, exact rehover persists, and the independent finance-window oracle
passes. The two calls report9,296 and10,178 input tokens; hover batches take
6.400s and full decision-to-evaluation33.920s. All126 v1/v2 frames and frozen
sources audit Windows/WSL. Retain as one accuracy/recovery candidate; layout/domain
transfer, token reduction and human tempo remain open. Subagent delegation is not
part of the evaluated path. See
[model-proposed active evidence](research/live_control/OPENTTD_ACTIVE_EVIDENCE_V2.md).

### First scoped target-handle allocation

A session-local candidate privately binds a named RGB region to focus, surface,
geometry, frame, observation and expiry. Ten synthetic controls cover valid,
revalidated, ambiguous, moved, missing, stale and scope-mismatch outcomes. A
first archive replay fails because its flat patch appears at both transformed
and untranslated positions; v2 refuses such low-information sources. In one
fresh same-session OpenTTD run, a textured handle correctly follows the window
manager's observed `[17,20]` client translation and derives point `[837,71]`
without caller coordinates. The click completes and releases in280.790ms, but
the preregistered endpoint expected requested delta `[16,0]` and no independent
semantic task effect exists. Retain as a negative/HOLD result. See
[scoped target handles](research/live_control/SCOPED_TARGET_HANDLES_V1.md).

A matched private Chromium pair corrects the endpoint design without changing
the matcher. Both sessions mint the same textured Save region and move the
client `[20,8]`. Positive revalidation derives `[290,251]` from the observed
binding and the independent HTTP/file oracle receives exact `t991005`; input ack
to useful frame/semantic completion is60.016/192.643ms. The changed-target case
navigates the same surface to `about:blank`, returns `MISSING`, admits zero
pointer input and creates no file. All36 frames audit exactly. Advance to a
different matched desktop task; no model, token or general identity claim.

A model-facing follow-up first exposes uncontrolled CLI usage and two
pre-model structured-schema failures, all retained. With a single action
envelope, short responder instructions, empty workspace and project-document
loading disabled, the fixed screen is4/4 correct and reports9,268 input tokens
for image coordinates versus8,009 for a no-image handle. The first fresh live
handle attempt then safely fails2/2 because the model returns a friendly name
while the registry requires a random private ID. A unique short session alias
repairs that interface fault. On new seeds, coordinate and alias-handle arms
independently submit2/2 each; model input is9,280 versus8,013 per call, both
handle query/admission checks are REVALIDATED, and62 frames audit exactly.
Handle needs16 durable calls versus14, and two cases/arm cannot establish causal
latency or broad compression. See
[target-handle live ABBA](research/live_control/TARGET_HANDLE_MODEL_LIVE_ABBA_V1.md).

The next candidate removes that handle-only round trip without weakening later
admission. `observe_target_handle` captures first and resolves the alias on the
same observation. A preregistered fresh Chromium pair saves2/2 independently;
combined versus separate observe/query uses12 versus14 durable calls and14 versus
15 exact frames. The combined check records the returned sequence/capture identity,
and admission revalidates again before input. All29 frames replay cross-OS. One
case per arm and no model calls establish no causal timing claim. A preregistered
OpenTTD transfer then uses the combined operation for Road Construction, passes
the local first-segment condition and independently completes the guarded five-tile
L with all four engine checks true. Its37 exact frames replay cross-OS. Geometry
and remaining actions are scripted, so model-boundary and changed-target tests
remain. See [combined observe-target](research/live_control/OBSERVE_TARGET_HANDLE_V1.md).

The model-boundary gate now passes on a fresh same-prompt seed991013 pair. Luna-low
returns the strict no-image alias action2/2 at8,013 input tokens. Stable revalidates,
independently saves and uses14 durable calls rather than the prior separate-query
handle path's16. In the paired stale case, the same surface changes to `about:blank`
after model return; admission yields `MISSING`, zero target-click pointer admissions,
verified release and no submission. All37 frames replay cross-OS. This is one
known task and a constructed target loss, with no causal latency or broad token claim.

The following seed991014 pair removes the manually transcribed absolute box from
the same target path. Identical Luna-low coordinate prompts return Save point
`[270,243]`2/2 at9,285/9,284 reported input tokens. The runtime derives a24x14
region from that point and retains source observation12. Stable matches a fresh
patch exactly, mints the unexposed private-ID-backed alias, follows surface delta
`[20,8]`, and a second no-image model call selects the alias at8,012 tokens. The
task independently saves exact `t991014`. Changed-target navigates to `about:blank`
after model return; source/current digests differ, so mint refuses before handle
creation with zero target pointer admissions. The35 exact frames, patch digests,
model configuration and outputs audit on Windows/WSL. Post-hoc contract review
finds that the prompt asks for screenshot-absolute coordinates while the caller
assigns `window_content` transformation membership. Hold promotion: frame and
region authorship, one known button and exact-pixel matching leave cross-domain
identity, token/cost benefit and human-tempo performance open. See
[model-point target derivation](research/live_control/MODEL_POINT_TARGET_V1.md).

The repaired seed991015 allocation asks the model to author numeric space and
motion separately. Identical controlled Luna-low calls return
`source_observation_pixels`, point `[270,243]` and
`surface_origin_translation`2/2, reporting9,264/9,265 input tokens. Stable maps
that motion to current runtime `window_content`, follows binding delta `[20,8]`
and independently saves exact `t991015`. Changed-target refuses a different fresh
patch before handle creation and target input. The audit reconstructs36 frames
and verifies source, prompt, schema, model contract, patch and output hashes on
Windows/WSL. This repairs the prior contract HOLD for the known task; caller-
authored24x14 size, cross-domain behavior and efficiency remain open. See
[explicit point and motion contract](research/live_control/POINT_TARGET_CONTRACT_V2.md).

The first explicit-contract transfer to a dense OpenTTD toolbar is a
preregistered failure. Both Luna-low calls author the correct point space and
surface-origin motion, but select `[650,51]` and `[432,51]` rather than the prior
independently successful Road Construction point `[820,51]`. The stable handle
faithfully tracks its wrong icon through observed binding delta `[21,28]`; the
first-road local condition then stops at step4 with12 target/0 guard changed
pixels and verified release. In the paired negative, opening the correct toolbar
does not alter the model-selected patch, so minting succeeds instead of refusing.
Independent task success is0/2 and all62 frames replay cross-OS. Preserve the
direct full-frame baseline; next test a bounded candidate set with delayed hover
labels and independent scoring. See
[OpenTTD point-contract transfer](research/live_control/OPENTTD_POINT_CONTRACT_V1.md).

The bounded hover-label follow-up separates semantic evidence from persistent
target identity. The first preregistered study proves the model selects the
correct Road Construction candidate but retains a failure: minting the hovered
patch includes 35 transient highlight pixels, so revalidation safely stops when
the highlight disappears. In the corrected pair, the pointer is cleared and
the original pre-hover patch must return exactly before mint. Rehover then
produces `MISSING` with zero target clicks, while stable follows surface delta
`[21,28]`, resolves `[841,79]`, completes all eight steps, and passes every
independent engine check. Tooltip semantics are3/3 across hover studies; the
corrected81 frames audit cross-OS. Reported input increases roughly636--640
tokens over the failed direct baseline and hover costs about3.6s. Retain the
candidate without a speed or generalization claim; next gate is uncertainty-
triggered probing on a held-out target or changed candidate layout. See
[OpenTTD hover target rebase](research/live_control/OPENTTD_HOVER_TARGET_REBASE_V1.md).

### First live bounded drag-effect allocation

A preregistered seed991003 replay keeps the v6 model, task, initial state,
checkpoint policy, turn limit and independent scorer, but appends path-local
before/after/absolute-difference panels after each drag. Fixed Astra recognizes
the A-to-B effect on turn6, immediately builds B-to-C and independently verifies
all five target tiles on turn7. It uses116,879 input tokens,26 durable calls,32
exact frames and109.034s from initial observation to semantic completion. The
retained v6 baseline failed after12 turns/199,613 tokens and two repeated A-to-B
drags; v7 repeats none. See
[live bounded effect evidence](research/live_control/OPENTTD_EFFECT_LIVE_V1.md).
The single sequential same-task result is retained for replication and does not
establish a causal percentage, geometry transfer or human tempo.

An unchanged preregistered replication is a hard failure. It builds A-to-B once,
marks the effect uncertain, performs two observation-only inspections and issues
a typed safe stop on turn8. It never repeats the completed A-to-B drag. Across
v7/v8 the candidate is1/2 for hard success and2/2 for preventing the specific
repeat mutation. The frozen failure also reveals that finish-outcome-v1 labels
every abort file `bounded_turn_limit`; explicit finish-kind v2 corrects the replay
to `typed_model_safe_stop` and keeps independent task success separate. See
[effect replication](research/live_control/OPENTTD_EFFECT_REPLICATION_V2.md).

Post-failure inspection finds that v8 discards the original drag panels after its
first observation-only turn. A bounded memory candidate retains one unresolved
drag and adds the latest inspection without accumulating history. Two
preregistered archived-context Astra-medium calls change checkpoint outcomes from
uncertain2/2 to observed2/2 and both choose the same B-to-C continuation; input is
33,655 versus34,419 tokens. Separate samples and no live execution prevent causal
or correctness claims. Advance only to a fresh live allocation. See
[effect memory](research/live_control/OPENTTD_EFFECT_MEMORY_V1.md).

The first preregistered fresh live memory episode succeeds. It builds A-to-B on
turn5, carries the uncertain effect across one inspection, marks it observed and
builds B-to-C on turn7, then repeats the inspect/observe transition and verifies
on turn9. The independent engine score passes all four gates; two observer
transitions change only the five target tiles and the final40/171 records remain
complete. It uses151,853 input tokens and153.027s, so it is slower than v7. Retain
for unchanged replication, without promotion. See
[live effect memory](research/live_control/OPENTTD_EFFECT_MEMORY_LIVE_V1.md).

The unchanged preregistered v10 replication also succeeds on turn9 with the same
checkpoint sequence and two distinct drags. Its observer changes only the five
target tiles, all17 terminals release input and the final37/180 records remain
complete. V9/v10 are2/2 hard success and2/2 zero completed-segment repeats. V10
uses151,842 input tokens and160.837s; both remain slower than v7. Advance to a
changed geometry without promotion. See
[memory replication](research/live_control/OPENTTD_EFFECT_MEMORY_REPLICATION_V2.md).

The first changed-geometry allocation moves the same L objective to a byte-pinned
seed991004 save and target tiles684,685,686,750,814. Two distinct drags complete
the task with no forbidden or surrounding changes and no repeated completed
segment. The first effect needs five inspection turns to become observed; the
second remains uncertain at the12-turn bound. The independent score succeeds,
but the controller never requests verification, so this is not hard success and
semantic completion time is absent. The run uses12 model turns,204,114 input
tokens,50 durable calls and195.604s model wait. It also exposes a supervisor
filename assumption after a successful limit score; a typed outcome selector
passes archived positive, negative and limit artifacts plus five refusal controls
on Windows/WSL. Hold pending completion feedback and packaging repair. See
[changed L geometry](research/live_control/OPENTTD_EFFECT_MEMORY_GEOMETRY_V3.md).

A pixel-only follow-up then measures persistent change inside the retained drag
crop without reading task or engine state. A posthoc threshold separates nine
selected first effects from two repeated completed-segment drags, but a
preregistered A/B/B/A model comparison rejects the prompt form. On the frozen
v11 turn7 context, exact-prompt Astra is `observed`2/2 and proposes progression;
the receipt condition is `uncertain`2/2, proposes inspection and adds156 input
tokens per call. No live input is issued. Keep the measurement only as a local
barrier candidate and separate evidence from action admission before retesting.
See [persistent visual-effect receipt](research/live_control/PERSISTENT_EFFECT_RECEIPT_V1.md).

Moving the same pixel condition into an already admitted program removes the
extra model call but fails the correctness gate. A fresh scripted X11 Inkscape
case requests a24px drag, reaches only12px, yet the163-pixel single-ROI condition
passes and starts the later Save step. A paired unmet case sees zero pixels and
correctly stops before Save; all seven frames reconstruct exactly and both
terminals verify input release. Reject total changed pixels as continuation
authority. The next condition must describe target-relative displacement or
separate target/guard structure. See
[local visual continuation barrier](research/live_control/LOCAL_VISUAL_BARRIER_V1.md).

A task-relative displacement condition repairs that specific correctness gap.
Its first fresh pair safely stops after exposing a wrong pointer-to-screen
assumption. A separately retained pair then uses settled source-relative anchor
tracking: a24px final displacement is present in both samples and admits Save;
a20px partial displacement returns `target_not_reached` and never starts Save.
The saved SVG,18 exact frames and both releases pass Windows/WSL audit. This is a
scripted moved-object condition; model authorship and a placement-specific
target/guard condition remain. See
[local displacement postcondition](research/live_control/LOCAL_DISPLACEMENT_POSTCONDITION_V1.md).

A preregistered fixed-context authorship probe then presents one exact source
frame and a mostly fixed postcondition schema. Luna-low and Astra-medium each
produce strict JSON2/2; all four authored patches cover the full red target,
accept both retained24px samples and reject both20px samples. Luna reports25,480
input tokens and Astra30,812 across two calls each, with no basis for a route
comparison. No GUI input is issued. Advance only to a fresh live transfer on the
same moved-object task. See
[model-authored displacement condition](research/live_control/LOCAL_DISPLACEMENT_AUTHORSHIP_V1.md).

The unchanged first Luna condition then transfers to fresh X11 processes. Two
preregistered predecessors retain a cross-OS path failure, partial pass, safely
released focus interruption and packaging assumption. Two later opposite-order
pairs both admit Save at24px and stop before Save at20px. All38 exact frames,
canonical authored identity, identical fresh sources, SVGs and releases audit on
Windows/WSL. A line-ending-sensitive preregistration failure is also retained
before input. Promote only as a same-task moved-object local postcondition
candidate; pointer paths remain scripted and no model call occurs in an episode.
See
[fresh authored-condition transfer](research/live_control/LOCAL_DISPLACEMENT_TRANSFER_V1.md).

A placement-specific condition then compares disjoint target and guard boxes.
The first preregistered archived allocation retains two false stops: samples
preceding the persistent road effect count against the condition. Requiring a
bounded settle immediately before evaluation repairs that contract without
changing boxes or thresholds. A separately preregistered v6/v7/v8 archive then
classifies all six engine-diagnosed effects: three first road segments are met,
two repeated completed-segment drags are target-not-reached and a later segment
inside the first condition's guard is guard-changed. Fresh X11 integration
separates target24px, partial20px and upward guard intrusion3/3 after one retained
focus interruption;28 frames, SVGs and releases audit on Windows/WSL. Retain for
fresh OpenTTD transfer with its independent scorer. Boxes remain human-authored
and no semantic success or speed claim follows. See
[local target-and-guard postcondition](research/live_control/LOCAL_TARGET_GUARD_POSTCONDITION_V1.md).

Fresh OpenTTD transfer first retains a driver-boundary failure: the program
omits the Road Construction opener, so both ordered allocations safely stop
without constructing A-to-B. A separately preregistered one-click correction
then passes its wrong-row/target pair, and an unchanged reverse-order replication
passes again. Across the corrected studies, target admits B-to-C and independently
completes the guarded L2/2; wrong-row stops before B-to-C2/2. All119 exact frames,
releases, process exits and save integrity audit on Windows/WSL. The condition
arrives about2.5s after the first drag in all four cases. Promote only as a
same-seed scripted local-continuation candidate; boxes remain human-authored and
no model, token, human-speed or geometry-generalization claim follows. See
[fresh OpenTTD target/guard continuation](research/live_control/OPENTTD_TARGET_GUARD_LIVE_V1.md).

The next candidate derives those boxes from the admitted two-segment pointer
path. Frozen seed991004 frames classify unchanged, first-segment and later-
segment states3/3. The first fresh preregistered negative is intentionally
retained as a failed control: a16px screen offset snaps to the same OpenTTD tiles,
so local and engine checks both correctly report task success. A separate
completed-segment repeat then returns `target_not_reached`, suppresses B-to-C and
keeps the independent score false. All106 fresh frames audit cross-OS. This
removes manual box transcription but uses a development-known path and does not
establish held-out geometry, model, token or human-tempo performance. See
[path-derived target/guard geometry](research/live_control/OPENTTD_TARGET_GUARD_DERIVED_GEOMETRY_V1.md).

Resolution transfer then rejects the assumption that one global translation can
move every pointer intent. At1280x720, `dx=+128` misses the map and `dx=-128`
moves map intent correctly but misplaces centered toolbar controls; both frozen
studies fail. Separating `screen_chrome dx=0` from window-origin-derived
`window_content dx=-128` passes a positive/repeat pair. Before observing a new
1152x720 run, the same rule predicts `dx=-64` and passes the reverse-order pair.
Corrected classifications are4/4 over135 frames; including failures,265 frames
audit exactly cross-OS. Local feedback remains2.46–2.60s and one seed/path is
reused. See [coordinate-frame resolution transfer](research/live_control/OPENTTD_COORDINATE_FRAMES_V1.md).

The next version moves that transform from the experiment runner into admission.
At1152x720, the runner sends original1024 coordinates with explicit frame IDs;
`executor_v4/session_v26` resolve clicks, drags and target/guard boxes from the
fresh binding, validate the raw program and emit resolution records before
execution. Fresh positive/repeat results agree with the engine2/2 over69 frames.
A separate post-admission surface move changes geometry before the first click;
the runtime returns `needs_decision` with zero pointer admissions,28.435ms after
the move and105.333ms after submit. See
[live binding-resolved framed intents](research/live_control/FRAMED_POINTER_INTENTS_V1.md).

### Retained OpenTTD effect-state diagnosis

The frozen seed991003 v6 run lacks a formal finish evaluation because its driver
exits before consuming the supervisor abort. Its continuous independent observer
log still proves partial state. Across263 records, one transition builds owned
road on A-to-B tiles977..979; the final172 records preserve it. B-to-C tiles
1043/1107 remain empty, forbidden and surrounding tiles remain valid, and the
hard score is false. The model repeats the same A-to-B drag on turns5,9 and11 and
never attempts the second leg. A bounded path crop measures3,628 changed pixels
on the first drag versus250/451 on the repeats, but semantic attribution remains
with the observer. See [effect-state diagnosis](research/live_control/OPENTTD_EFFECT_POSTHOC_V1.md).
This is one archived diagnostic, not a live interface improvement or speed claim.

### Process-scoped end-to-end timing envelope

Path: [`research/live_control/TIMING_ENVELOPE_V1.md`](research/live_control/TIMING_ENVELOPE_V1.md).
A fresh Calc task saves and independently verifies480/192 in three Luna/low
turns. One supervisor clock measures23.976s from initial observation detection
to semantic completion, including21.334s of wrapper-observed model waits; two
proposal-to-useful-feedback intervals are1.105s and0.873s. Missing provider,
runtime and OS endpoints remain explicitly unrecorded. Per-event fsync is rejected
after isolated median record costs of5.264ms Windows/8.702ms Linux. Buffered v2
reduces record medians to18.1/14.718us plus one close-time sync, with weaker
crash durability. No speedup follows from this single episode.

The OpenTTD follow-up adds bounded delayed-hover observation, contact sheets
that preserve multiple intermediate tooltip frames, content-derived action
timeouts and a fixed adaptive model route. Luna-low alone fails the guarded road
task after nine turns; two subsequent fresh adaptive runs pass the independent
target/connectivity/forbidden-row/surrounding checks. The first positive run then
fails result packaging on an obsolete field name; the corrected fresh v8 run
completes its envelope in111.853s, including91.781s of wrapper-observed model
wait across eight calls. It reports126,420 input tokens,44 exact frames and28
durable calls. Windows and WSL artifact audits pass. This is one corrected
adaptive episode plus one positive task effect, not a matched speedup or
human-tempo result. See
[OpenTTD TimingEnvelope](research/live_control/TIMING_ENVELOPE_OPENTTD_V1.md).
A preregistered matched follow-up then runs one fresh fixed-order episode per
route with the same canonical save, task, nine-turn limit and evaluator. Fixed
Luna fails after nine turns and changes three surrounding guard tiles. Fixed
Astra passes in98.351s with7 calls and114,186 reported input tokens; adaptive
passes in100.201s with8 calls and126,424 tokens. All141 exact frames and88
durable calls audit across Windows and WSL. This rejects promotion of the authored
adaptive route, but one episode per arm cannot promote fixed Astra or establish
a latency distribution. A reversed-endpoint second block reproduces fixed-Astra
success and fixed-Luna failure, while adaptive falsely declares visual completion
and fails the independent score. Cumulative hard results are Astra2/2,
adaptive1/2 and Luna0/2. The newly exposed driver assertion is replaced by an
explicit negative finish outcome candidate and a three-path artifact regression.
See [matched model replication](research/live_control/OPENTTD_MATCHED_MODELS_V2.md).
A preregistered v3 follow-up then validates both finish paths on fresh fixtures.
The zero-input/no-model control preserves a negative independent score as a typed
failure with driver exit0; a normal fixed-Astra run passes in92.377s with6 calls
and97,729 input tokens. Fixed Astra is now3/3 on this same task, with a descriptive
95.219s mean. Windows/WSL audit passes; different tasks remain required. See
[typed finish outcome](research/live_control/OPENTTD_FINISH_V3.md).
A preregistered follow-up changes one initial-state factor: Road Construction is
opened before the timed observation while the canonical save, task, prompt,
fixed-Astra route and engine guard stay fixed. The model independently succeeds
in89.272s with6 calls,97,696 input tokens,24 exact frames and20 durable calls.
The prior closed-toolbar episode used6 calls and20 durable calls as well.
Toolbar discovery disappeared, but targeting confirmation occupied the freed
boundary. The descriptive3.105s difference is not a causal speedup. See
[changed initial UI](research/live_control/OPENTTD_INITIAL_STATE_V4.md).
A new seed-991002 fixture then changes the byte-pinned save, map contract and
visible target position. A geometry-derived scorer preserves the prior outcomes,
rejects six malformed/change controls and evaluates target465..467 with a
42-tile guard. The preregistered zero-input negative control passes, followed by
a fixed-Astra hard success in89.097s. It uses7 calls,114,177 input tokens,32
frames and24 durable calls: one more planner boundary and four more calls than
the prior geometry. Shorter model waits mask this extra interface work in total
wall time, so no speedup is claimed. See
[new geometry transfer](research/live_control/OPENTTD_GEOMETRY_V5.md).

### Actual pixel redaction with explicit unknown semantics

Path: [`research/live_control/REDACTED_OBSERVATION.md`](research/live_control/REDACTED_OBSERVATION.md).
On one fresh Chromium source frame, four full-image Luna/low calls read the exact
field value and four redacted-image calls returned `UNKNOWN /
REDACTED_BY_POLICY`; no post-observation action was allowed. V2 declares half-open
box semantics and its changed-pixel bound matches the policy box. One hundred
renders measured 38.757 ms median and 46.917 ms p95. Explicit metadata increased
reported input by 112 tokens/call, so this is not compression evidence. The
ambiguous v1 geometry, a fixed-filename measurement failure, and platform PNG
encoding differences are retained. Task action around hidden regions and bypass
resistance remain open; no broad privacy claim follows.

A follow-up action study uses six fresh same-seed Chromium sessions. Full,
unmarked-redaction and explicit-redaction conditions each complete the adjacent
visible Save task 2/2, reach VERIFIED, and pass independent scoring. All click
points lie inside the declared Save target and outside the hidden field; the four
redacted model calls disclose no secret. Explicit input is 9,454 tokens versus
9,341 full and 9,306 unmarked. Since the unmarked control also passes and there
are only two samples/condition, no metadata or latency advantage is claimed.
Sixty-six frames replay exactly. The live harness omitted gate timestamps; an
isolated 10,000-call gate measurement is 3.769us median/4.379us p95.

A required-target mutation follow-up uses one fresh episode per condition. Full
observation admits the model's five-step replace-and-Save program and independently
succeeds. Unmarked and explicit redaction both make the model stop; the gate
refuses, no post-observation input is submitted, and the private current value is
absent from model I/O. Inputs are 9,364/9,329/9,477 and 32 frames replay exactly.
This promotes the zero-input fail-closed rule only; one sample per condition and
voluntary model stops do not show an explicit-marker advantage or actual unsafe-
proposal rejection. An unsupported-uppercase setup failure is retained.

A policy-race follow-up uses two fresh seed-253 sessions with byte-identical full
presentation prompts. Luna/low proposes the same `replace_and_save` mutation in
both. Under the unchanged `full-control` policy, the five-step program reaches
VERIFIED and independent success. In the other session, the policy changes only
after the model returns to `hide-current-text-entry` version 2. The proposal's
bound version no longer matches, so the gate returns `policy_binding_mismatch`,
submits zero post-observation input, and leaves the task intentionally incomplete.
Both calls report 9,359 input tokens; 23 frames replay exactly and the Windows
and Linux audits pass. This establishes refusal of one actual stale model
proposal before input. Because the full image was already disclosed before the
policy tightened, it is not evidence that the transition retroactively protects
confidentiality. Alternate observation/history bypass remains open.

An authorized-refinement follow-up keeps the hidden pixels byte-identical while
changing the policy and observation identity. With no mutation authority the
first Luna/low call stops and no input follows. Version 3 then authorizes only
whole replacement by the exact public task value and one Save target. The second
call proposes that operation; the gate admits five steps, the effect verifies,
and independent evaluation passes without exposing the prior value to either
model call. Replaying the proposal against the previous binding refuses. Inputs
are 9,432/9,529 tokens; 15 frames replay exactly; eleven altered-authority
controls and Windows/Linux audits pass. This does not authorize append, partial
selection, inference, alternate-channel access, or general hidden-field control.

Pre-model controls then bind that live artifact into a single-current-view
bundle. Thirteen crop/history/raw-image/OCR/UI-tree/clipboard/binding/digest/
authority variants refuse with zero model calls and GUI actions. Eight proposal
shape variants likewise prevent whole-replacement authority from expressing
append, insert, partial selection or caller-defined steps. Cross-OS audit passes.
This is an offline boundary over one archived artifact, not proof of OS isolation,
provider retention behavior, or every future observation channel.

### Compact planner evidence, caller binding and partial terminals

Path: [`research/live_control/`](research/live_control/COMPACT_PLANNER_EVIDENCE.md).
Sixteen fixed-image model calls preserved 8/8 expected decisions in both full and
compact conditions while reported input fell 3.33%. One fresh compact-driven
Chromium action then completed with independently verified saved output and two
lost checkpoint replies recovered without resend. The newer v3 presenter binds
the checkpoint to the caller's expected request ID and completion contract;
nine adversarial identity/contract controls refuse before model delivery. A
partial-evidence model comparison is retained as confounded because its common
prompt disclosed the fact removed from one condition. A corrected Chromium
fixture then produced one real visually silent delayed effect: same-image model
calls with execution evidence wait/check 4/4, while checkpoint-only calls submit
once 4/4. This establishes decision relevance for those fields in one declared
case. A fresh live follow-up then used one strict model wait/check while the effect
completed, reaching VERIFIED with no post-UNKNOWN input or extra sleep. Two newer
same-seed sessions expired before versus after Return. The model submitted once
for the 3/6 prefix and waited for the 4/6 prefix; only the former admitted new
input, and both reached independent success. The ten queries needed after the new
submission expose missing event-driven effect readiness. None of this establishes
general reliability, human tempo, privacy-safe redaction or default adoption.
A same-seed no-model A/B then moves the bounded effect polling into one verifier
request: post-UNKNOWN durable calls fall from 10 to 1 and completion detection
from 5,060.458 to 4,897.769 ms. The verifier still performs 97 filesystem samples,
so this is round-trip reduction rather than event-driven readiness or CPU savings.
A fresh model-driven follow-up preserves submit-once versus wait/check across the
partial Return boundary and uses one bounded query after either decision. On the
fresh-submission path, post-decision queries fall from 10 to 1 and total durable
calls from 17 to 8 versus the previous live route. Model-time variation prevents
a causal end-to-end latency claim, and explicit v6 provenance adds about 20 input
tokens.

Primary artifacts:

- [`COMPACT_PLANNER_EVIDENCE.md`](research/live_control/COMPACT_PLANNER_EVIDENCE.md)
- [`COMPACT_LIVE_FORM.md`](research/live_control/COMPACT_LIVE_FORM.md)
- [`PLANNER_EVIDENCE_BINDING.md`](research/live_control/PLANNER_EVIDENCE_BINDING.md)
- [`DELAYED_EFFECT_DECISION.md`](research/live_control/DELAYED_EFFECT_DECISION.md)
- [`DELAYED_EFFECT_LIVE.md`](research/live_control/DELAYED_EFFECT_LIVE.md)
- [`PARTIAL_TERMINAL_LIVE.md`](research/live_control/PARTIAL_TERMINAL_LIVE.md)
- [`EFFECT_WAIT.md`](research/live_control/EFFECT_WAIT.md)
- [`PARTIAL_TERMINAL_WAIT.md`](research/live_control/PARTIAL_TERMINAL_WAIT.md)

### First DOOM-engine transfer

Path: [`research/doom/`](research/doom/README.md). The assistant used X11 screenshots
and OS keys in ViZDoom/Freedoom's basic room, reaching completion in two development
runs. An async-clock probe is consistent with 35 tics/second; 50 recorded frames
audit exactly across three operated sessions. Initial window, cached-telemetry
and binding failures are retained. This is not full-game or human-speed evidence.

### Moving-screen tracking — local visual motor feedback

Path: [`research/visual_tracking/`](research/visual_tracking/README.md).
Twelve frozen synthetic X11 episodes compare the same pixel-based policy at
50 ms local updates versus 250/1000 ms decision cadence. All completed with
verified release; application-side scoring favored local updates in all six
pairs. One assistant-selected local method also completed. This is a narrow
dynamic motor study, not LLM inference overlap, generic GUI understanding,
human comparison or a DOOM result. Failures and raw scoring records are retained.

### Live control — asynchronous functional prototype

Path: [`research/live_control/`](research/live_control/README.md).
A separate command reader and GUI worker support early feedback, held inputs,
cancellation and verified key release. The latest six scripted XTerm/Calc
probes passed with 54 exact frames. Local cancel-to-release observations ranged
from 0.50 to 20.79 ms; this is not model end-to-end latency or a speedup claim.
An actual assistant cancellation arrived after the program ended; the raw
failure and successful GUI recovery are retained. Intent expiry and stale-state
guards remain necessary before claiming dependable real-time planner control.

### Real Apps v1 — input delivery and sparse observation

Path: [`research/real_apps_v1/`](research/real_apps_v1/)

Apps: XTerm, Chromium, LibreOffice Calc, Inkscape.

What it established:

- fixed `100 ms` sleeps do not guarantee correctness;
- input delivery and application consumption are different events;
- Calc required about `1 ms` character pacing in the tested X11 setup;
- Inkscape long-run drag stability improved when the press-to-motion barrier was increased from the short-screen `2 ms` candidate to `5 ms`;
- sparse/reactive observation can cut full-screen observation substantially while improving success in the development screen.

Primary artifacts:

- [`results/REPORT.md`](research/real_apps_v1/results/REPORT.md)
- [`results/real_app_summary.csv`](research/real_apps_v1/results/real_app_summary.csv)
- [`real_app_suite_v1.py`](research/real_apps_v1/real_app_suite_v1.py)

### Real Apps v2 — semantic method lifetime vs route lifetime

Path: [`research/real_apps_v2/`](research/real_apps_v2/)

Question: when an optimized route fails, should the semantic method be discarded too?

Result: not by default. Across three fresh Inkscape replicates (72 episodes total), keeping the semantic method while suspending/reheating only the route preserved 72/72 success while reducing method redefinition churn, planner-byte proxy, and visual observation.

Primary artifacts:

- [`REAL_APP_SELF_COMPILE_V2_REPORT.md`](research/real_apps_v2/REAL_APP_SELF_COMPILE_V2_REPORT.md)
- [`route_suspend_summary.csv`](research/real_apps_v2/route_suspend_summary.csv)

### Real Apps v3 — Guarded Hierarchical Deoptimization

Path: [`research/real_apps_v3/`](research/real_apps_v3/)

Question: if a fast route has observable dependencies, can we avoid predictable failures before executing the route?

Result: yes, in the tested X11 cases.

- XTerm focus guard: 72/72 success; failed routes eliminated; p99 reduced by about 77.5%.
- Chromium geometry guard: 72/72 success; failed routes eliminated; p99 reduced by about 75.4%.
- Chromium binding replacement + geometry drift: semantic method remained valid while binding was repaired and route deoptimized independently.

Primary artifacts:

- [`GUARDED_HIERARCHICAL_DEOPT_REPORT.md`](research/real_apps_v3/GUARDED_HIERARCHICAL_DEOPT_REPORT.md)
- [`GHD_ALGORITHM_SPEC.md`](research/real_apps_v3/GHD_ALGORITHM_SPEC.md)
- [`guarded_hidden_summary.csv`](research/real_apps_v3/guarded_hidden_summary.csv)
- [`complete_hidden_summary.csv`](research/real_apps_v3/complete_hidden_summary.csv)

## Observation Gating — A1 scoped result

Path: [`research/observation_gating/`](research/observation_gating/)

On 2026-09-13 JST, frozen A1 revision 3 completed two fresh replicates, 24 paired
episodes/app across XTerm, a Chromium-family browser (Chrome for Testing), Calc
and Inkscape under Ubuntu/WSL2/Xvfb. O0 and O1 each achieved **96/96 success**.
All **1,446 sampled frames** reconstructed exactly, with zero false suppressions
or missed sampled changes.

- Exact same-trace image reduction: **17.15%**, 95% pair-bootstrap interval
  **13.86–20.65%**.
- Live intended-model-boundary images: **722 → 604**, **16.34%** reduction
  (12.14–20.64% interval). The receiver is a local reconstructing sink; no LLM
  was invoked.
- Median paired local task-wall delta (O1 minus O0): **+0.59 ms**, interval
  **-2.36 to +4.73 ms**. A speedup was not established.
- O1 exact compare cost: p50/p95/p99 **0.025/0.337/0.729 ms** per sample.

Decision: **PASS as a scoped O1 research baseline**, enabling the next O2
experiment. This is not a user-runtime promotion or evidence of token savings.
Captures still happen, and benefits differ strongly by application.

The result retains a rejected Calc startup-grey screen and two earlier frozen
Inkscape baseline failures. A visible selection barrier alone did not repair the
drag failure. The final local policy uses a conservative 30 ms press dwell,
validated with both pair orders; it is not a universal input specification.

Primary artifacts:

- [`REPORT.md`](research/observation_gating/REPORT.md)
- [`PROTOCOL.md`](research/observation_gating/PROTOCOL.md)
- [`DEVELOPMENT.md`](research/observation_gating/DEVELOPMENT.md)
- [`summary.csv`](research/observation_gating/results/a1r3-summary/summary.csv)
- [`frozen source and environment`](research/observation_gating/results/frozen-a1r3/)

## Observation tiles — A2 scoped result and actual assistant use

Path: [`research/observation_tiles/`](research/observation_tiles/).

On 2026-09-13 JST, frozen A2 revision 2 completed **64/64 fresh episodes**, eight
O1/O2 pairs/app across the same four real apps. All **553 sampled frames** passed
independent archived-wire/raw-PNG reconstruction and saved-output checks.

- Same-trace serialized-byte reduction: **70.73%**, 95% pair-bootstrap interval
  **64.72–75.19%**. Both representations use identical zlib level 1 and metadata.
- Live bytes: **13,562,871 → 3,853,968**, **71.58%** reduction.
- Paired task-wall delta (O2 minus O1): median **+2.00 ms**, interval
  **−4.00 to +12.27 ms**. A local speedup is not established.
- Full images are reconstructed before controller/model viewing. This does not
  establish image-token savings, and captures still occur in full.

Revision 1 stopped at a baseline Inkscape drag failure after 31 attempts; its
entire fresh efficacy comparison is retained as rejected. Revision 2 adds a
shared segmented gesture with observations while the button is held. This does
not isolate motor reliability from pacing and is not adaptive path correction.

The parent assistant also directly used the new stdin research interface to
operate Calc, Inkscape and XTerm through reconstructed screenshots. These three
exploratory sessions led to bounded change waits, unchanged PNG reuse, explicit
image/context timestamps, command logs and atomic unsupported-text rejection.
All three outputs and 18 observations were re-verified. This is actual use, but
not a controlled model latency/token comparison or a universal runtime.

Decision: **PASS for exact transport research; HOLD for a speed/token/runtime
claim**. A bounded Luna sourcing/review pilot was useful but needed fresh-source
verification after stale findings; no controlled model ranking was obtained.

Primary artifacts: [report](research/observation_tiles/REPORT.md),
[protocol](research/observation_tiles/PROTOCOL.md),
[failures and actual use](research/observation_tiles/DEVELOPMENT.md),
[primary-source research](research/observation_tiles/RELATED_WORK.md), and
[fresh summary](research/observation_tiles/results/a2r2-summary/summary.json).

### Continuing hypothesis

Image preparation was subsequently isolated in an [offline replay study](research/observation_tiles/IMAGE_ARTIFACT.md).
On the two archived A2 replicates, exact PNG reuse reduced local preparation
time by 10.81% / 16.59%; PNG level 1 instead of level 6 reduced reuse-path time
by a further 15.89% / 16.03%, with larger PNG files. All 1,659 validation outputs
decoded exactly. This is not new live-task, model-token or end-to-end evidence.
The shared sink is integrated into dogfooding with an explicit compression option;
the default remains 6. Actual assistant use at level 1 completed XTerm correctly,
but revealed a roughly 10.22-second inter-command interval despite local images
being ready in 41–56 ms after action issue. The next priority is the real
agent/tool interaction boundary, not further isolated image micro-optimization.

The next major question is whether image feedback can be treated as a local state-change signal rather than automatically forwarding every screenshot to a model.

Candidate ladder:

```text
O0 full screenshot after each step
O1 exact/fast unchanged-frame suppression
O2 + spatial change vector / changed-tile mask
O3 + relevant-region gating
O4 + local VERIFY
O5 + persistent visual state + ROI delta
O6 + GHD deterministic-route observation skip
```

The primary metric should be:

> percentage of model-visible image observations eliminated while preserving the same task correctness.

Secondary metrics: observed pixels, false update detection, missed update, local compute time, tail latency, and escalation rate.

## Promotion policy

A candidate is promoted only when:

1. correctness is not worse under the defined hard gate;
2. parameters are frozen before hidden/fresh evaluation;
3. baseline and candidate see the same task/environment schedule;
4. result survives at least one fresh replicate or explicitly remains `HOLD`;
5. claims are scoped to the actual environment measured.

## Claims taxonomy

| Term | Meaning in this repository |
|---|---|
| `planner bytes` | serialization byte proxy, **not tokens** |
| `observed pixels` | pixels captured/processed by the harness, **not image tokens** |
| `wall time` | local harness timing, **not model-in-loop latency** |
| `hidden/fresh` | task/seed not used to tune the candidate; not a security claim |
| `real app` | actual desktop application under X11/Xvfb, not a synthetic widget model |

## Rejected or held ideas

Negative results are retained because they constrain the design space.

- fixed sleeps as a correctness mechanism — rejected;
- method-wide invalidation for every route failure — rejected as default;
- blind re-anchor-and-continue — unstable in fresh runs;
- aggressive predicted ROI without clipped-observation rejection — caused centroid bias/failures;
- event filtering across a high-frequency Python/stdio boundary — observer overhead erased gains;
- replacing all observation with a single global perceptual hash — insufficient for local motion/change.

## Next experiments

1. Paired agent-in-the-loop adapter measurement: PNG/reference reuse, real image tokens and resume latency.
2. Isolate adaptive motor feedback from additional pacing/observation cost; retain the failed drag regression.
3. Longer mixed-app sessions with app restarts, focus drift, geometry drift, and modal transitions.
4. ROI/visual-state experiments with full-base recovery, plus guard placement cost vs expected failure cost.
5. Only after algorithmic semantics stabilize: production-oriented implementation work.

The first changed-objective OpenTTD allocation is now frozen. A seed-991003
five-tile L fixture and independent 49-tile guard pass cross-OS replay, but the
preregistered Astra episode stopped before pointer input because the new driver
violated the durable journal's identity-assignment contract. The rejection,
single model proposal, observation-only calls and traceback are retained. A
separately preregistered corrected allocation executes eight actions, then
produces a typed false visual completion: the B-to-C leg is correct, the A-to-B
leg is absent, and a four-tile road appears one map row above it. It spends
146,736 reported input tokens and 148.339 seconds before the rejected verify.
This newly exposes target-binding/visual-assurance weakness; see
`research/live_control/OPENTTD_L_OBJECTIVE_V1.md`.

A visual-only two-times before/after crop around the failed drag was then tested
against the exact full frame. Both fixed-Astra calls judge the A-to-B alignment
`uncertain`; the composite uses 526 more reported input tokens. The crop is not
promoted. Since the full frame expresses uncertainty when explicitly asked for
subgoal status, the next mechanism is a semantic checkpoint that blocks a new
mutation until the prior expected effect is observed, contradicted or uncertain.

That checkpoint now has one fresh live allocation. It prevents a second task
mutation and false verify, but the model makes five uncertain inspections and
stops on turn 11 after 182,284 input tokens. The task remains false and the
frozen v1 parser mistakenly rejects the safe stop; checkpoint v2 corrects that
shape boundary. A zero-model Ctrl+2 probe verifies a recovery affordance from
the official OpenTTD manual: trees become transparent while all road, owner,
guard and save state remains unchanged. Typed planner access and fresh recovery
efficacy remain untested.

Typed access now has one fresh fixed-Astra allocation. It invokes the tree
transparency method three times, makes no second task mutation and safely stops
on turn 12. The independent task remains false, while all target, forbidden and
surrounding road-owner state is unchanged. This contains the prior off-target
failure but costs 198,746 input tokens and does not recover correctness. Because
Ctrl+2 is a toggle, the three calls alternate presentation state and expose a
missing idempotent postcondition.

Two preregistered zero-model diagnostics narrow the remaining failure. Across
six fresh restores, the known -16px path reproduces the off-target 912..915
roads, while offsets -12 through +4 build intended tiles 977..979. Offset 0 is
the failed model path. With offset 0 fixed, combined selection/drag, an immediate
program boundary and a 15-second boundary all produce the same intended effect.
Neither coordinate invalidity nor sampled tool-state delay explains the model
episode's zero effect. `semantic_checkpoint_v4` replaces the toggle-shaped
method with a tracked `ensure_trees_transparent` transition, permits proactive
use and refuses repeats or unknown state. Fresh model efficacy and general
view-state detection remain open.

The proactive transition now has a preregistered live allocation. It changes
the view in428.854ms with two durable calls and zero added model boundaries.
Fixed Astra uses7 turns/115,045 input tokens instead of v4's12/198,746, but
falsely verifies after building A-to-B one row high; B-to-C is correct.

A second preregistered allocation adds only the official, general sign-to-map-
square relation. It makes12 action proposals, consumes199,613 input tokens and
never verifies or safely stops. At the turn limit the driver raises before
consuming the supervisor abort, so no formal finish evaluation is emitted. The
continuous observer later proves a stable partial A-to-B result and missing
B-to-C leg; the run remains hard-false. See the retained effect-state diagnosis
above.

Driver v5 now closes the limit-path race. A zero-model, zero-pointer live probe
applies12 observe-only proposals and then obtains a scored
`bounded_turn_limit` outcome through50 durable calls;39 observations, release,
save, task state and exit0 audit cross-OS. The fix preserves failure evidence and
makes no task-performance claim.

Ctrl+1 sign-transparency feasibility also transfers from the seed991003 L task
to the held-out seed991002 straight geometry. Both zero-model probes preserve
independent road/owner state and save bytes while changing custom sign
presentation. Full-frame deltas include normal simulation progress, so the
method is not promoted. Next freeze a paused or temporally matched pair before
testing model targeting and independent task correctness.

The paused held-out probe removes that contamination: its consecutive stability
frame changes zero pixels and Ctrl+1 changes1,151/1,024,000 while preserving
task/save state. A preregistered fixed Astra A/B/B/A targeting diagnostic then
passes2/2 in both opaque and transparent conditions, with30,572 input tokens per
condition. The transform yields no measured coordinate or token benefit and is
not promoted. Direct endpoint grounding is already correct in this isolated
question; next investigate live tool/effect-state evidence.

Verified active-hover evidence now has a compact presentation result. A frozen
Luna-low Full/Compact/Compact/Full comparison holds prompt, schema, receipt set
and target constant. All4 calls bind receipt5 `[485,51]`; full reports10,170
input tokens twice and compact8,274 twice, reducing the mean by1,896/18.64%.
The compact builder admits only tooltip crops whose RGB digest matches the
runtime receipt and retains ordinary input admission as a separate boundary.
Windows/WSL audits pass. Scope is one fixed OpenTTD task, with no broad GUI,
dynamic latency or human-tempo claim. See
`research/live_control/OPENTTD_COMPACT_EVIDENCE_ABBA_V1.md`.

The compact path then runs in one fresh translated-window episode. The actual
OpenTTD surface moves `[21,28]`; a screen-wide single-pass detector finds the
moved toolbar at row68 with30 slots in154.287ms. Luna-low proposes `[506,79]`,
selects its verified compact finance receipt, rehovers exactly and opens the
window. The shifted independent RGB oracle passes after29.639s from decision
start. Inputs are9,294+8,277 and the five persistent hovers take6.199s. All50
frames and raw turns audit Windows/WSL. This is one position transfer, not
resize/reflow, unknown-app generality or human tempo. See
`research/live_control/OPENTTD_TRANSLATED_COMPACT_LIVE_V1.md`.

Anchor-first evidence next tests one receipt before five-slot acquisition. A
frozen Luna-low Correct/Wrong/Wrong/Correct study accepts the finance anchor2/2
and requests expansion on the retained confidently-wrong anchor2/2. Fresh live
use normalizes `[505,79]` to `[506,79]`, accepts its verified tooltip, rehovers
and passes the shifted oracle. Initial hover falls6,198.997->1,283.273ms,
durable calls16->14 and frames50->39. Sequential total time is25.964s versus
29.639s and is not a causal latency estimate. Fixed and live evidence audit
Windows/WSL. The implemented expansion route remains unproven live. See
`research/live_control/OPENTTD_ANCHOR_FIRST_EVIDENCE_V1.md`.

The bounded expansion route now recovers one preregistered deterministic wrong
anchor. Archived `[436,51]` translates and normalizes to `[456,79]`; Luna-low
returns `EXPANSION_REQUIRED` from its single receipt, receives four additional
verified neighbours, then selects `[506,79]`. The only button-down occurs after
selection; exact rehover, release and the shifted finance oracle pass. The run
uses18 durable calls,50 exact frames and8,107+8,280 input tokens, with24.956s
from decision start to evaluation. Windows/WSL audit passes. The separate v1
preflight path failure remains preserved. This is injected recovery capability,
not natural error frequency, causal speed or cross-domain evidence. See
`research/live_control/OPENTTD_WRONG_ANCHOR_RECOVERY_V2.md`.

The anchor-first evidence path now transfers to Mindustry's dense4x4 build
palette. A retained formal v1 failure shows the OpenTTD compact builder rejecting
a verified314x100 Conveyor panel at its fixed62px row before semantic decision or
click. Shared size-aware v2 preserves the small OpenTTD presentation exactly and
adapts the Mindustry row. In a new fixed allocation, Luna-low `[1004,578]`
normalizes to screen-derived `[1007,577]`; one click-free receipt is bound and the
only button-down selects Conveyor. Hover caller reply is909.187ms, semantic
selection20.771s, independent selection oracle23.538s, and model inputs
9,300+8,115. Six exchanges/15 frames and both raw turns audit Windows/WSL. This
is fixed-layout selection, not placement, causal speed or human tempo. See
`research/benchmark_discovery/MINDUSTRY_ANCHOR_FIRST_SELECT_V2.md`.

The next Mindustry step separates palette-control evidence from world-target
evidence and completes one target outside the earlier route. Four first-allocation
failures are retained while output contracts are corrected: a schema/validator
relation mismatch, unsupported candidate and receipt `oneOf`, and a missing
explicit property type. V5 uses flat typed points arrays, bounded palette binding
and an animated placement-preview receipt. Luna-low's four calls use34,967 input
tokens; the run has14 socket exchanges,33 exact frames and exactly two button
admissions. Independent engine scoring verifies target orientation, one-copper
cost, unchanged112-tile guard, source/core and paused idle completion. Runtime
world feedback is457.934ms and placement feedback270.075ms; full completion is
53.463s with39.023s parent-observed model time. Windows/WSL audit passes. Issue
#54 tracks endpoint schema preflight. This is one positive fixed-screen case, not
a reliability, speedup, compression or human-tempo result. See
`research/benchmark_discovery/MINDUSTRY_SINGLE_TILE_LIVE_V5.md`.

The output-schema boundary now has a preregistered actual-endpoint preflight.
Two retained invalid schemas are refused before any completed turn; three
corrected schemas complete and use23,674 input tokens in total. Same-identity
cache reuse makes no fresh call, and Windows/WSL audits confirm zero GUI
artifacts. This is client/model compatibility evidence only: the server revision
is not exposed, the first checks are token-expensive, and live input authority
is not gated yet. See
`research/live_control/SCHEMA_PREFLIGHT_V1.md`.

The follow-up schema-authority block covers the remaining Mindustry receipt
`oneOf`: the actual endpoint refuses it in3,625.993ms with no completed turn or
usage. The corrected three-schema set passes from pinned cache without a fresh
call. A Mindustry v6 wrapper now places this gate before its GUI continuation;
the actual-cache ordering test calls that continuation0 times after refusal and1
after acceptance. Live positive/no-match/ambiguous evidence is still required.

The schema-gated three-condition Mindustry block now supplies that live evidence.
Positive independently succeeds; viewport-excluded and unreadable cases admit
no placement and preserve engine state. The block is formally false because the
first negative returns coordinate-free `ambiguous` rather than the predeclared
no-match reason. Eleven calls report96,731 input tokens;70 exact frames and28
socket exchanges audit Windows/WSL. Retain safety evidence and the taxonomy
failure without retry. See
`research/benchmark_discovery/MINDUSTRY_SINGLE_TILE_MATCHED_V1.md`.

Evidence selection now has a candidate operational authority split. Positive
verified-receipt decisions return `TARGET_REFERENCE_ONLY`; no-match, ambiguous,
unavailable and exhausted results return `NO_TARGET_AUTHORITY` with no receipt
or coordinates, preserving the diagnostic separately. Retained OpenTTD and
Mindustry evidence plus four invalid controls pass. A fresh endpoint preflight
accepts the flat schema with 7,916 input tokens; no fresh GUI efficacy is claimed.
See `research/live_control/EVIDENCE_TARGET_CONTRACT_V2.md`.

Fresh OpenTTD validates the authority split. V1 first exposes a context-loss
failure: removing the concrete target noun makes Luna accept the injected wrong
anchor, though zero buttons are issued. V2 keeps the target at both boundaries;
Company Finances selects receipt5 and passes its independent oracle, while an
Airport target absent from all five receipts returns `NO_TARGET_AUTHORITY` and
zero target buttons. Four calls use 32,992 input tokens and 93 exact frames audit
cross-OS. See `research/live_control/OPENTTD_EVIDENCE_AUTHORITY_PAIR_V2.md`.

Mindustry now revalidates receipt-bound pixels from a fresh post-model
observation before target input. The unchanged condition independently places
one Conveyor; changed palette, changed world and changed focus refuse the
affected input. The four-condition block uses 12 model calls, 115,443 input
tokens, 44 exchanges and 75 exact frames with no retry or subagent. Its formal
result remains false because the focus control produced the more specific
`focus_or_surface_changed` diagnostic rather than preregistered
`current_evidence_unavailable`, while still returning no authority or point.
See `research/benchmark_discovery/MINDUSTRY_RECEIPT_REVALIDATION_V1.md`.

The receipt revalidation follow-up now covers the previously missing live
unavailable-binding and resize branches. An override-redirect InputOnly X11
focus produces a real `pointer_binding: null`; temporary EWMH unmaximize
produces a real Mindustry surface-size change. Both return typed no-authority
outcomes, admit zero target buttons and restore the original binding/geometry.
The passing block uses four calls, 34,806 input tokens, 20 exchanges and 15
frames; two setup failures remain visible. See
`research/benchmark_discovery/MINDUSTRY_RECEIPT_REVALIDATION_FOLLOWUP_V3.md`.

Adaptive acquisition now has one offline shared caller for cold acquisition,
warm reuse, invalidation and repair. It records attempts before model adapters,
keeps completed calls separate, derives field-level usage coverage without
zero-filling and marks omitted stages/comparison class. Fifteen retained-record
and test-double branches pass Windows/WSL audit: full cold anchor and expansion,
injected subpath, no-match/exhaustion, stale/association refusal, reuse/repair,
missing or partial usage and duplicate IDs. The 0-call reuse and 1-call repair
are mechanics only, not measured savings. See
`research/live_control/ADAPTIVE_ACQUISITION_CALLER_V1.md`.

Issue #56 now supplies the next integration target. The #53 caller should
measure a compiled GUI interface that retains bounded symbols, predicates,
guarded actions and invalidation rules after grounding. A decisive mechanics
case needs at least two observe/action transitions where fresh intermediate
local evidence changes the next authorized action without another frontier
model generation. Symbols remain evidence references, never input authority.
The first finite live comparison should use an existing independently scored
desktop fixture and report plain, current-optimized and compiled cold/warm/
invalidation/repair costs through the same caller; a Mindustry layout follows
as the different-domain check. No efficiency or break-even claim exists yet.

The deterministic compiled-interface boundary now exists. It validates bounded
symbols, explicit predicate effects and method branches; obtains new admission
for every action; and yields on unknown/ambiguous state, stale evidence/symbol,
association change, no progress, failed effect, cancellation, budget, uncertain
delivery or release failure. A Calc-shaped positive performs two fresh-evidence-
dependent actions with zero model resumptions. Fifteen test-double scenarios
pass independent Windows/WSL audit through the #53 caller. Raw evidence retention
and all live efficiency/correctness claims remain unproved. See
`research/live_control/COMPILED_GUI_INTERFACE_V1.md`.

The first full Issue #57 comparison now measures the integrated path. Under one
preregistered six-task sequence, plain, compiled-ephemeral and compiled-persistent
all score 6/6 exact once. Charging one fresh endpoint-schema call to each arm,
cumulative input is 63,128/63,779/26,563 and generations are 7/7/3; persistent
crosses below both references at task 2. It safely refuses the old layout-A
reference before task-4 input, repairs once, and finishes in 44.131s versus
56.412s/73.238s. Seventeen actual calls and all releases reconcile in Windows
and WSL audit. This RETAIN decision applies to the fixed workflow and allocation,
not broad token savings or human-speed performance. See
`research/live_control/INTEGRATED_EFFICIENCY_LIVE_V1.md`.
