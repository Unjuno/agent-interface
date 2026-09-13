# Local research handoff — 2026-09-13

## Latest follow-up — actual Calc checkpoint use separates displayed and saved cells

[Calc checkpoint self-use](../research/live_control/CHECKPOINT_CALC_SELF_USE.md)
returns UNKNOWN while the format modal remains and the saved cells are empty,
then VERIFIED after confirmation; both retain task_success=null. Explicit finish
independently succeeds. Twelve frames, two released programs and all 27 records
pass audit. Query roundtrips are 16/17 ms, but outer boundaries remain 27 seconds
before confirmation and 23 seconds before finish; no speedup claim. The pre-save
artifact bytes were not retained separately. No conditional finish is implemented.

## Latest follow-up — sleeping checkpoint does not prevent live cancellation

[Checkpoint cancellation](../research/live_control/CHECKPOINT_CANCEL.md) gates
the verifier while a real Chromium hold executes. A second query reports busy;
cancel returns matched and terminal/release completes before the gate is released.
The same-process cancel roundtrip is 34.219 ms in one run. Two frames and the
17-record prefix audit pass. A raw cross-process interval lacks the probe clock
descriptor and is explicitly rejected by the audit. CPU/GIL/output contention
and hard cancellation bounds remain unproven; no default promotion.

## Latest follow-up — non-final checkpoint permits confirmation after UNKNOWN

[Effect checkpoint](../research/live_control/EFFECT_CHECKPOINT.md) adds optional
runtime v29/socket v14 artifact queries in a single asynchronous worker. A scripted
browser run samples UNKNOWN before confirmation, admits correction, then samples
VERIFIED with task_success=null; explicit finish independently succeeds. Twenty-two
frames, full prefixes, release and retained attempt logs pass. The first transport
allowlist failure is retained. Missing/mismatch/error/busy and request identity
controls pass. This is not a full effect contract, universal verifier or default
promotion; actual self-use, Calc and slow-verifier/cancel interaction are next.

## Latest follow-up — premature-finalization counterexample reproduced

[Confirmation boundary comparison](../research/live_control/CONFIRMATION_BOUNDARY.md)
uses the same scripted fixture and input sequence with only the first submit
boundary changed. Premature outcome fails and rejects later confirmation;
terminal review permits confirmation and succeeds. Sixteen/twenty-two exact
frames, full prefixes, lineage and release pass. The v2 attempt archive survives
both complete GUI cleanups. No admission-preserving verifier has been implemented;
Issue #34's broader effect contract remains open. Current client guidance now
states explicitly that outcome requests closure, not an ordinary effect query.

## Latest follow-up — confirmation recovery succeeds; expiry and log loss retained

[Confirmation self-use](../research/live_control/CONFIRMATION_SELF_USE.md) adds a
visible second confirmation requirement. Actual assistant use completes it with
three admitted programs, 21 exact frames and correct independent evaluation.
An unplanned expired request adds a clock refresh and explicit new attempt; six
socket calls and 128967 ms total capture-to-flush retain that recovery cost.
The auxiliary HTTP attempt log was lost during cleanup. A v2 fixture fixes its
destination and passes a separate survival probe; no retroactive reconstruction.
Keep finalization deferred for known additional decisions; unfamiliar completion
and admission-preserving evaluation remain unresolved.

## Latest follow-up — combined report/image delivery removes a display-only turn

[Combined image self-use](../research/live_control/COMBINED_IMAGE_SELF_USE.md)
returns full action records and the referenced original image within one outer
tool result. Actual assistant form replacement passes independent scoring and
13-frame/release/lineage checks. The outer form boundary was 17475 ms versus
22003 ms previously, but one sequential pair and different visible report text
do not isolate speedup. Runtime/caller remain unchanged. Keep the combined display
recipe for further self-use; next test larger tasks or new recovery cases.

## Latest follow-up — actual self-use exposes a 22-second outer boundary

[Browser endpoint self-use](../research/live_control/ENDPOINTS_BROWSER_SELF_USE.md)
uses v6 after actual initial/form image inspection. Correct submission, 13 exact
frames, release, request lineage and direct-final drain skip pass. Caller main to
stdout flush is 992/459 ms; form flush to next main is 22003 ms, with model/tool
components unseparated. No matched speedup or model receipt claim. Next test
displaying the received image in the same tool result as the send/wait response.
The corrected initial app-selector launch error is retained separately.

## Latest follow-up — caller preparation and response processing now have endpoints

[Client endpoints](../research/live_control/CLIENT_ENDPOINTS.md) adds optional
prepared_exchange_v6 phase marks and a final sidecar after stdout flush. Model
receipt/generation timestamps remain explicitly null. A scripted gated Calc run
passes 12-frame, saved effect, release, lineage and early/final checks. Preparation
and persistence take measurable tens of milliseconds in this WSL run; no causal
attribution or speed claim. Preserve v5 and the current default candidate. Next
use the marks in actual self-use and controlled storage comparisons.

## Latest follow-up — actual reply batching weakens the compression case

[Delivered clock cost](../research/live_control/DELIVERED_CLOCK_COST.md) replays
seven distinct recorded socket replies, preserving the entire response exactly.
Savings fall to 4.024%; empty and single-record replies grow. With deep-copy
packing included, paired CPU increases are about 50 microseconds for encoding
and 46 microseconds for decoding per reply. Keep the codec offline; no protocol
change or default promotion. This is one scripted Calc trace, not a token or
live-latency result. Prioritize caller boundary costs and missing timing endpoints.

## Latest follow-up — clock metadata has measurable byte overhead

[Clock metadata cost](../research/live_control/CLOCK_METADATA_COST.md) measures
the same 52 raw events: repeated clock IDs add 4524 bytes (12.880%). Paired local
JSON CPU changes are sub-microsecond/record, with no live latency inference.
An offline shared-domain batch codec round-trips all records and reduces the
equivalent JSON array by 4396 bytes (11.073%); four negative controls pass.
No live transport or token savings claim. Next measure delivered-batch costs
and preservation of cursor/gap semantics before any integration.

## Latest follow-up — clock domain identity prevents unsupported interval claims

[Timing clock](../research/live_control/TIMING_CLOCK.md) records Linux boot/time
namespace/offset/implementation identity in runtime v28 and caller v5 (socket v12).
Two processes and a full scripted Calc run match domains; four invalid/missing
controls return no duration. Twelve exact frames and saved result still pass.
Issue #46 remains partial: model endpoints, overhead and matched OpenTTD coverage
are missing. No retrospective clock labels or synthesized model times are added.

## Latest follow-up — browser final result skips the optional drain

[Browser drain self-use](../research/live_control/DRAIN_BROWSER_SELF_USE.md)
uses candidate v4 for actual visible draft replacement. Final evaluation returns
directly, attempted=false, with no drain request. Three socket calls and thirteen
exact frames audited; total processing endpoint 47.961 s, outer form gap 13.934 s.
No speedup claim. README now links a [current client guide](../research/live_control/CURRENT_CLIENT.md)
that consolidates versions, tested paths and missing product/performance evidence.

## Latest follow-up — optional drain has a shared absolute I/O deadline

[Drain socket deadline](../research/live_control/DRAIN_SOCKET_DEADLINE.md) replaces
the optional drain's 35 s socket timeout with a 250 ms absolute connect/send/read
budget in candidate prepared_exchange v4. Real socket stall/trickle controls
return around 251 ms and retain early evidence; four other cases pass. Full
Calc gated-evaluation integration still passes with twelve exact frames. Initial
send timeout is unchanged; this is not a hard wall-time or model-latency bound.

## Latest follow-up — integrated CLI returns early while final evaluation is gated

[Live drain delay](../research/live_control/LIVE_DRAIN_DELAY.md) verifies the full
CLI returns effect_observed/unknown task success while a real evaluator gate is
closed, then its continuation receives final success after release. Twelve exact
frames, saved workbook, source hashes, release and full prefix audited. Candidate
v3 adds explicit producer attribution for scripted tests. This covers responsive
socket delay, not blocked I/O or human timing. The drain remains optional.

## Latest follow-up — early and final Calc results returned in the same caller

[Final drain self-use](../research/live_control/DRAIN_FINAL_SELF_USE.md) adds opt-in
zero-server-wait final read after early result processing. Actual same-seed Calc
returns both records in one confirmation invocation; caller commands 4→3, socket
count unchanged at four. Thirteen exact frames and full prefix audited. Early to
processing-end is 34.275 ms; total 45.541 s with missing model receipt endpoint.
No causal speedup claim. Six controls pass; next test integrated live delayed
evaluation to validate returning early when a final result is not yet available.

## Latest follow-up — actual Calc use exposes an avoidable outer final-read turn

[Prepared Calc self-use](../research/live_control/PREPARED_CALC_SELF_USE.md)
validates terminal→visible dialog→outcome with two prepared programs and twelve
exact frames. Early result arrives at 48.084 s; final read at 66.408 s. Final
evaluation emits just 12.862 ms after early evidence, yet its next client starts
18.319 s later. Missing model endpoints remain explicit (Issue #46 not fulfilled).
Next test an optional immediate final drain in the same caller while retaining
all records and preserving early return on genuinely delayed evaluation.

## Latest follow-up — combined prepared send/wait used by the assistant

[Prepared exchange self-use](../research/live_control/PREPARED_EXCHANGE_SELF_USE.md)
combines preparation and send/wait in one CLI and preserves exact requests/replies.
Same seed/steps as prior token task: one exchange replaces two; three exact frames
and saved result audited. First capture to socket return 27.448 s, outer initial
decision interval 13.097 s. Sequential single runs and differing final timing
boundaries do not prove causal speedup. Next exercise a branching GUI case.

## Latest follow-up — build actual input requests without evidence-field copying

[Prepared self-use](../research/live_control/PREPARED_SELF_USE.md) derives sequence,
delivery ID and historical deadline from received evidence and explicit steps.
Three prior commands regenerate exactly; four malformed controls rejected. Actual
assistant xterm use succeeds with three exact frames and no copied runtime fields.
Total 36.649 s vs earlier 36.125 s: no speedup evidence. This is a preparation
component; transport invocation remains separate. Next reduce measured caller
overhead rather than repeatedly optimizing the already short local program.

## Latest follow-up — actual visual replacement of pre-existing browser text

[Prefilled self-use](../research/live_control/PREFILLED_SELF_USE.md) introduces a
known draft in the local browser fixture. Assistant views it, selects all and
replaces it; only the requested token is saved. Two programs, twelve exact frames,
release and complete received prefix audited. Total 52.626 s; form-to-admission
14.672 s; client wait 184.588 ms. Planned adaptation, not unexpected recovery or
speedup evidence. Next vary selection/focus without announcing the repair route.

## Latest follow-up — live pending status advances with a fresh query

[Status transition](../research/live_control/STATUS_TRANSITION.md) tests correct
and wrong input with gated ordinary evaluation. Initial fallback returns pending;
exact old-query replay remains pending without a new command; a fresh query
returns available with true/false evaluation. One submit, two status commands,
three exact frames per case and input release audited. Scripted coverage, not
model latency evidence. Next use the client in an actual visible recovery case.

## Latest follow-up — bounded outcome CLI used by the assistant

[Outcome client self-use](../research/live_control/OUTCOME_CLIENT_SELF_USE.md)
adds a transcript-preserving CLI and uses it after actual image-based xterm
input. Saved token and independent evaluation match; three exact frames,
release and eleven-record prefix audited. Client wait 81.423 ms, but total
first-capture-to-client-return 36.125 s. No fallback query was needed and no
speedup is established. Live pending-to-available remains the next missing test.

## Latest follow-up — caller performs a bounded, identity-checked status fallback

[Outcome fallback](../research/live_control/OUTCOME_FALLBACK.md) adds candidate v2:
one outcome read plus at most one fresh status query after timeout. Both direct
outcomes and status validate the expected program, separately from query identity.
Live evaluator-fault integration uses two fallback calls without resubmission;
three exact frames and release audited. Ten controls pass. V1's omitted direct
program check and its narrow evidence are preserved. This bounds call count, not
arbitrary exchange wall time. Next test live pending-to-available and self-use.

## Latest follow-up — request-scoped status queries including concurrent callers

[Status correlation](../research/live_control/STATUS_CORRELATION.md) adds query
identity in interactive v27 and supports it via boundary v2/cursor v5/socket v11.
Live evaluator-fault test matches concurrent replies and verifies exact-query
replay causes no new command. Three exact frames, one submit, release and returned
prefix slices audited. Four identity controls pass. Task success stays unknown.
Next implement bounded status fallback: fresh snapshots require new query IDs,
and final_program must be checked independently from query identity.

## Latest follow-up — live evaluator exception recovered through retained status

[Failed outcome wait](../research/live_control/FAILED_OUTCOME_WAIT.md) injects an
evaluator exception after real private X11 input. The generic wait returns pending;
sequential status queries retrieve the same evaluate-stage finalization_error,
without rescore or resubmit. Three exact frames, verified release, full prefix,
one submit and clean process exit audited. Task success stays unknown. Error is
retained at 19.587 ms and status received at 235.190 ms after terminal (including
chosen 200 ms wait). Status response currently lacks query identity: add that
before making fallback automatic or supporting concurrent status reads.

## Latest follow-up — live delayed outcome continuation without input replay

[Live outcome wait](../research/live_control/LIVE_OUTCOME_WAIT.md) exercises the
common policy through socket v10 and actual private X11 input. A test evaluator
gate yields pending in about 101 ms; releasing it returns true for the correct
token and false for a wrong one (ordinary scorer takes about 3 s on mismatch).
Both cases have one submit, three exact frames, verified release and complete
response prefixes. Scripted fault injection, not assistant latency evidence.
Next cover a finalizer exception where no final outcome event is published.

## Latest follow-up — common read policy for optional early effects

[Outcome wait policy](../research/live_control/OUTCOME_WAIT.md) waits for either
request-scoped early effect or final evaluation. An early effect retains its
scope and supplies a final-only continuation; unsupported early effects no
longer force waiting when final evaluation is present. Twelve replay/control
cases pass, including delayed completion without command replay and false,
missing or malformed outcomes. Candidate helper only, no live latency claim.
Next integrate with a live caller and test delayed/failed finalization.

## Latest follow-up — actual browser use exposes completion coverage gap

[Browser receipt self-use](../research/live_control/RECEIPT_BROWSER_SELF_USE.md)
successfully navigates and submits a local form after image inspection. Two
programs, one clock, three socket calls, twelve exact frames; independent result
returned 52.728 s after initial capture. Form decision gap remains 15.999 s.
Unlike Calc, Chromium emits no early effect_evidence: callers must request the
supported independent evaluation outcome. Next make completion capabilities or
fallback explicit and test delayed/failed outcomes. This is an existing simple
desktop fixture, not a new benchmark domain or evidence of human-like speed.

## Latest follow-up — receipt-selected images used in a live Calc episode

[Actual receipt image self-use](../research/live_control/RECEIPT_IMAGE_SELF_USE.md)
saves the expected cells with two programs, one clock, no failed image view,
and twelve exact audited frames. First-capture-to-effect socket return is
48.495 s versus the prior 61.548 s; modal socket-return-to-admission is 13.540 s.
These uncontrolled sequential episodes do not establish a causal speedup.
The modal viewer now consumes the selector result in the same orchestration call.
Next test a different visible decision/recovery case; avoid overfitting this save.

## Latest follow-up — select images from received references

[Receipt image selection](../research/live_control/RECEIPT_IMAGE.md) replaces
filename guessing with explicit observation references. Twelve known batches
and four negative controls pass; the receipt-clock modal selects `006.png` and
was visually inspected. Historical replay only: no new live latency claim or
default architecture promotion. Next apply it at a live caller boundary.

## Latest follow-up — one less clock call does not yet improve total self-use time

[Receipt clock self-use](../research/live_control/RECEIPT_CLOCK_SELF_USE.md) uses
existing terminal time for a new bounded confirmation deadline with unchanged
runtime checks. Actual Calc save succeeds, twelve exact frames audited; clocks
fall 2→1 and caller operations 5→4. Modal gap falls 24.658→20.654 s, but initial
delay grows and total effect-read time increases 57.082→61.548 s. A guessed image
filename failed then was corrected from the receipt; failure time is retained.
No speedup claim. Next measure/streamline observation handling and outer tool gaps.

## Latest follow-up — actual request-scoped Calc effect and final result reads

[Request outcome self-use](../research/live_control/REQUEST_OUTCOME_SELF_USE.md)
exercises socket v10/EventCursor v4 with actual assistant image inspection and
two Calc programs. Terminal, early effect and final score retain confirm request
identity; saved cells, twelve exact frames and replay suppression audited. Five
caller operations, 57.082 s first-capture-to-effect-read, 24.658 s modal gap; no
speedup claim. Six identity/rejection controls pass. Next use this lineage for
end-to-end decision-boundary comparisons rather than more metadata-only tuning.

## Latest follow-up — accepted request identity persists through completion

[Admitted lineage](../research/live_control/ADMITTED_LINEAGE.md) binds receive
metadata only on actual executor acceptance in interactive_v26/socket v9. Two
rejected attempts then a valid attempt reuse one action label; accepted, terminal
and final score point only to the valid transport request. Saved token, three exact
frames and owner close audited. Calc early-effect attachment is not yet exercised;
request-scoped terminal consumption, full causal lineage and bounded retention remain open.

## Latest follow-up — transport/runtime rejection identity survives concurrent attempts

[Request identity](../research/live_control/REQUEST_IDENTITY.md) connects private
socket v8 request IDs to interactive_v25 command/rejection records and optional
request-scoped reads. Two concurrent rejected submits share one action ID but
return distinct matched request identities. Same-ID replay does not resend;
payload conflict/reserved-field injection reject before runtime. Subsequent token
save succeeds, source/frame/owner-close audit retained. Scope remains local process
lifetime; terminal/effect attempt lineage and restart identity are not established.

## Latest follow-up — runtime rejection correlation avoids stale parsed IDs

[Rejection correlation](../research/live_control/REJECTION_CORRELATION.md) adds
per-input-line runtime sequence and bounded caller-declared IDs in interactive_v24.
Two live cohorts cover five rejections then successful token save; the second
actually advances observations before testing stale admission. Bad JSON/arrays
do not inherit prior action identity. Command/rejection joins, frames and owner
close audited. Socket request-ID mapping and concurrent-reader use remain open;
do not interpret reused caller action IDs as unique rejected attempts.

## Latest follow-up — action-scoped event reads avoid wrong-terminal boundaries

[Action-scoped events](../research/live_control/ACTION_SCOPED_EVENTS.md) adds an
explicit identity map in EventCursor v2/socket v7. Frozen actual Calc replay now
waits through enter_save to confirm_excel while preserving the entire prefix.
Missing/conflicting IDs and unattributed rejection return explicit uncertainty.
Live scoped xterm cancel/retry passes (49 ms response), two exact frames audited.
Runtime rejections still lack request correlation; next address that without
guessing ownership from arrival time. Optional candidate, no default promotion.

## Latest follow-up — socket failure path distinguishes transmission states

[Socket pipe fault](../research/live_control/SOCKET_PIPE_FAULT.md) adds typed
rejected_before_write / write_uncertain / channel_unusable receipts in v6.
Actual socket-to-paused-runtime test preserves normal sending after pre-write
rejection, reports 4096/8028 partial bytes in 101 ms, suppresses retry and later
cancel writes, then observes expired/released terminal and normal exit. Source,
frame and owner-close audit retained. This closes the direct-pipe-only evidence
gap; permanent reader stall/restart and action-bound event matching remain open.

## Latest follow-up — live pipe integration preserves expiry during stdin pause

[Live pipe expiry](../research/live_control/LIVE_PIPE_EXPIRY.md) integrates an
exclusive unbuffered writer in private socket v5; ordinary cancel/retry passes.
A separate real-runtime fault pauses stdin two seconds, writes 4096/8031 bytes,
times out at 100 ms, and closes stdin. Hold expires/release verifies while reading
is paused; partial EOF JSON rejects and runtime exits normally. Twelve exact
frames and owner close audited. Socket failure reply itself is not yet fault-tested;
generic write_uncertain recovery wording conflates validation and poisoned pipe.
Next distinguish those states and exercise the end-to-end socket fault.

## Latest follow-up — bounded pipe writes expose partial-command uncertainty

[Bounded pipe writer](../research/live_control/BOUNDED_PIPE_WRITER.md) adds an
unintegrated nonblocking writer. Actual 4096-byte Linux pipe tests retain full
and partial-write timeouts at ~100 ms, with the latter sending 4096/4234 bytes.
Both poison the channel so later cancel cannot corrupt a partial JSON record;
this does not deliver cancel. Unicode and closed-reader controls pass. Initial
oversize probe failure is preserved separately. Next integrate exclusive
unbuffered stdin and test shutdown/lease behavior; no default promotion.

## Latest follow-up — saturation requires separately reserved cancel capacity

[Socket saturation](../research/live_control/SOCKET_SATURATION.md) confirms eight
active observation handlers cause normal cancel to return busy. Private v4 adds
two cancel-only slots on a separate socket; under the same saturation key release
occurs before any long read ends. First cancel attempt to verified release is
1764 ms in v3's wait/retry policy versus 27 ms via v4's reserved endpoint. Twenty-four
exact frames and actual key admission/release audited. Shared blocked stdin and
cancel-slot saturation remain unresolved; no universal latency claim or promotion.

## Latest follow-up — live observation wait blocks cancel; bounded concurrency helps

[Socket cancel delay](../research/live_control/SOCKET_CANCEL_DELAY.md) retains
serial v2 failure: a two-second read delays cancellation response 1988 ms and
verified key release 1976 ms. Bounded eight-handler v3 yields 49 ms response and
93 ms release while the read still waits. Actual key admission, release and 22
exact frames audited; live disconnect/retry clock is not duplicated. First v3
startup-timeout driver failure retained as cohort 02; corrected same-process
wait completes cohort 03. Saturation/control reservation and blocked stdin remain
unverified; no broad latency guarantee or default promotion.

## Latest follow-up — combined send/wait reduces caller operations in self-use

[Send/wait self-use](../research/live_control/SEND_WAIT_SELF_USE.md) adds private
event_socket_v2 command forwarding and session-local at-most-one write attempts.
Actual assistant Calc use saves 532/590; repeated confirmation ID does not resend.
Caller operations through final result fall from 10 to 5, first-capture-to-effect
read is 57.422 s versus prior 77.053 s (sequential/familiar, not causal A/B).
Twelve exact frames and complete prefix audited. Unit duplicate/uncertain-write
controls pass; live disconnect, restart and cancel blocking remain unverified.
Next test those transport failure boundaries before promotion.

## Latest follow-up — actual socket reads separate results but add overhead

[Event socket self-use](../research/live_control/EVENT_SOCKET_SELF_USE.md) records
actual assistant Calc control with inherited stdin and read-only local socket.
Effect/final results arrive through separate tool calls; six read batches match
the entire 25-record prefix, saved values and twelve exact frames verified.
First capture to effect read is 77.053 s; no speed gain shown. Final already
existed before the early read returned. Next combine send/wait in one caller
operation, then test slow readers/disconnects; private transport only.

## Latest follow-up — retained event-prefix reads separate early/final results

[Event cursor](../research/live_control/EVENT_CURSOR.md) adds a bounded private
Condition-based reader returning through a requested event while retaining later
records. Two live scripted Calc sessions preserve complete stdout prefixes;
unsaved early return precedes final return by 3010.867 ms. Replay, interruption
prefix, explicit eviction gap, timeout and close/drain controls pass. This is
local supervisor evidence, not earlier model wakeup. Next expose a local session
transport for one bounded caller read and exercise it in actual self-use.

## Latest follow-up — actual assistant use exposes outer delivery boundary

[Early effect self-use](../research/live_control/EARLY_EFFECT_SELF_USE.md) records
actual image inspection and two assistant Calc programs through interactive_v23.
Saved 532/590, no rejection; twelve exact frames/artifact hash/receipts audited.
Runtime final-terminal to early emit is 20.295 ms, but early and final results
arrive in one tool response. Modal-to-confirm boundary is 15.899 s and total
first-capture-to-effect is 38.723 s. No causal A/B or human-speed claim. Next
measure event-aware outer delivery instead of optimizing only runtime emission.

## Latest follow-up — early saved-effect publication removes scorer wait

[Early saved effect](../research/live_control/EARLY_SAVED_EFFECT.md) connects
interactive_v23 to separate effect_evidence before independent scoring. Matched
scripted unsaved case emits effect at 18.585 ms versus v22's 3023.367 ms; final
scoring still emits at 3032.829 ms. Save remains correct. Fourteen exact frames,
early/final receipts and four callback failure/UNKNOWN controls audited. This is
runtime emit timing, not assistant recognition latency. Next actual self-use and
live output faults; synchronous blocked-output risk remains. No default promotion.

## Latest follow-up — live finalization carries scoped saved-effect evidence

[Live saved effect](../research/live_control/LIVE_SAVED_EFFECT.md) connects the
candidate to interactive_v22 finish_after. Two scripted Calc episodes complete
their programs but return distinct VERIFIED / CONTRADICTED effects. Fourteen
exact frames and flush receipts audited; callback UNKNOWN/failure retention passes.
Unsaved effect computes in 15 ms but combined evaluation emission waits 3023 ms,
identifying the next delivery bottleneck. Initial wrong settle-field rejection
is retained separately. Next separate early effect delivery from final scoring;
no assistant speed claim, default promotion or freeze credit.

## Latest follow-up — scoped three-way saved-effect evidence

[Saved effect](../research/live_control/SAVED_EFFECT.md) introduces a private
first-sheet cell predicate with VERIFIED / CONTRADICTED / UNKNOWN. Eight frozen
route artifacts distinguish five saved from three unsaved endpoints; six controls
cover missing/corrupt evidence, an open window, formulas, collateral B1 change
and a matching sample. This is artifact replay, not live causal attribution or
planner acceleration. Next integrate at an explicit finalization boundary with
program terminal retained separately. No default promotion or freeze credit.

## Latest follow-up — route-specific focus, movement and occlusion failures

[Modal target routes](../research/live_control/MODAL_TARGET_ROUTES.md) compares
Return and coordinate click in eight private X11 Calc trials. Click saves after
internal-focus change but stops on movement and is swallowed by a same-surface
child overlay; Return fails internal-focus change but saves in those latter
conditions. Fifteen exact public frames, saved artifacts and overlay button
events audited. The moved-click owner revision advances for an attempted rejected
operation, so revision is not a physical-input count. First-step-bound guard v3
is a private candidate only; no semantic target identity, route promotion or
freeze credit. Next evaluate explicit effect outcomes across this failure matrix.

## Latest follow-up — live check/input race falsifies target binding

[Modal check/input race](../research/live_control/MODAL_CHECK_INPUT_RACE.md)
retains a control and a post-check internal-focus mutation against frozen guard
v2. Both pass the guard and terminate completed with verified release; only the
control saves XLSX values. The negative opens ODF Save as while X11 binding stays
unchanged. Four exact public frames, diagnostic samples and independent workbook
contents audited. Fault-injection timings are not natural race rates or assistant
speed. Issues #34/#45 support separating verified effects from target revalidation;
next compare target-addressed activation with movement/occlusion negatives.
No guard promotion or freeze credit.

## Latest follow-up — actual X11 pre-input modal guard

[Live modal guard](../research/live_control/LIVE_MODAL_GUARD.md) connects a private
one-shot proposal guard to shared Backend/Executor Return. Normal case saves;
internal focus, geometry, age and session negatives stop with needs_decision and
unchanged input revision. V1 copied session identity incorrectly and lacked guard
images; v2 corrects/retains both cohorts. Eleven public frames/five guard samples
audited. Check→input is not atomic, display name is not runtime incarnation, and
no planner boundary is yet removed. Core candidate only; no freeze credit.

## Latest follow-up — bind modal proposals to explicit observation dependencies

[Bound modal proposal](../research/live_control/BOUND_MODAL.md) associates the
visual candidate with immutable session/sequence/time/window/focus/geometry and
image digest. Four frozen image cases and synthetic dependency/age negatives pass.
Pass means requires_new_admission, no input authority. This is offline consistency,
not live race prevention; next wire trusted context sampling to ordinary admission
and preserve the distinction between prepared proposal and authorized execution.

## Latest follow-up — fresh modal translations preserve focus discrimination

[Modal translation](../research/live_control/MODAL_TRANSLATION.md) tests two
predeclared new positions with Excel/ODF focus, four real images. Fixed coordinates
reject all; observed-geometry translation accepts Excel and rejects ODF with the
same source/threshold. Replay, stale-offset and bounds controls pass. Fresh variant
within known family, no autonomous input. Next bind window/frame/age dependencies
and revalidate any prepared branch at ordinary admission.

## Latest follow-up — modal focus counterexample before speculative control

[Modal predicate](../research/live_control/MODAL_PREDICATE.md) collects actual
Calc checkbox/ODF/Excel focus variants sharing X11 focus ID/window list. Broad
modal similarity accepts wrong keyboard targets; an additional button-region
comparison rejects them in nine known image cases. Candidate returns no authority
and no semantic verification. No autonomous branch or speedup claimed. Next freeze
fresh variants and admission dependencies; generic appearance cannot authorize Return.

## Latest follow-up — live finalizer faults and status recovery

[Live finalizer faults](../research/live_control/LIVE_FINALIZATION_FAULTS.md)
inject pre-write failure, post-flush failure and scorer exception in actual X11
processes. Six scripted tasks preserve saved content/release; 18 frames audited.
Interactive_v21 exposes read-only retained finalization_status, tested twice after
each fault without additional score output. Visible bytes can coexist with an
unconfirmed flush. Permanent outages/pending-query behavior remain unqualified.
Next return to earlier modal planner gaps while keeping oracle scoring post-controller.

## Latest follow-up — finalization failures separate from task outcome

[Finalization failures](../research/live_control/FINALIZATION_FAILURES.md) adds
stage-specific status to interactive_v20. Seven callback fault cases distinguish
unknown evaluation, task false and output failure; computed results survive publisher
errors. A real X11 scripted cancellation episode records task false with successful
finalization. Status file/stderr are best effort, not durable guarantees. Blocked
I/O, live publication-error injection and status-query design remain open.

## Latest follow-up — final-program scoring removes a benchmark request boundary

[Final scoring](../research/live_control/FINAL_SCORE.md) adds finish_after to
experimental interactive_v19. Actual same-task Calc passes; final terminal→score
known is 17.317 ms versus prior explicit-finish 30.650 s. Forty matched-task frames
audited. Timing is runtime-side and total speedup is confounded. Oracle remains
post-controller: reservation rejects later programs and closes admission before
scoring; finish is cleanup only. Invalid reservation/cancelled final task tested,
with an initial compact-event wait failure retained. Finalizer I/O/error delivery
and general semantic verification remain unqualified.

## Latest follow-up — same-task examples comparison shows no total speedup

[Calc examples comparison](../research/live_control/CALC_EXAMPLES_COMPARISON.md)
repeats actual self-use with the same seed/goal and accepted steps. Both score
correctly; 39 frames audited. Rejections 1→0 and submit commands 3→2, but first
capture→score stays 97.873→97.515 s as other external gaps grow. This sequential,
familiar pair cannot causally attribute differences to examples. Shift priority
from local micro-optimization to declared planner-boundary/verification latency,
using fresh-admission constraints for any speculative preparation experiment.

## Latest follow-up — Calc self-use and basic-operation discovery

[Calc self-use](../research/live_control/JOURNAL_CALC.md) uses interactive_v17
to enter two cells and handle Excel format confirmation from terminal receipt
imagery. Saved values pass, 19 frames/33 delivery pairs audited. An initial wrong
chord shape was rejected before input and is retained. Interactive_v18 now includes
validator-checked basic examples in ready (not yet live-tested); full schema
discovery and matched task-speed comparison remain open.

## Latest follow-up — serialized journal and actual assistant integration

[Journal integration](../research/live_control/JOURNAL_INTEGRATION.md) resolves
the probe ordering issue: four real X11 stalls preserve receipt order and release
input while cancellation notification is blocked. Interactive_v17 uses persistent
receipts and advertises decision evidence fields. Actual assistant xterm self-use
passes saved-token scoring; total fifteen exact frames across self-use/stalls.
No matched task-speedup or complete disk-error/concurrency qualification. Next
evaluate the integrated entrypoint on matched tasks or an orthogonal domain.

## Latest follow-up — journal stall integration exposes ordering failure

[Journal stalls](../research/live_control/JOURNAL_STALL.md): initial cohort 01
failed at Inkscape setup; cohort 02 verifies physical/owned release while write
or flush is blocked under expiry/cancel, with no late continuation. Write/cancel
reorders receipts because the probe concurrently calls a single-writer journal.
Ordering failure is retained and reproduced by audit; no runtime adoption.
Next serialize probe emission and move cancel invocation to an independent caller,
checking authority cancellation despite blocked notification delivery.

## Latest follow-up — persistent receipt file isolates open/close cost

[Receipt journal](../research/live_control/RECEIPT_JOURNAL.md) preserves per-record
flush while opening once. Twenty matched blocks of 15 identical receipts show
92.125→7.424 ms median persistence time, persistent faster 20/20; byte equality
and write/partial-write/flush failure controls pass. These are filesystem-only
measurements, not live GUI/model speedup. Journal failure is sticky, not rollback.
Next integrate with teardown and held-input output-stall tests; default runtime
and authority behavior are unchanged.

## Latest follow-up — matched delivery cost and bounded reference candidate

[Delivery cost](../research/live_control/DELIVERY_COST.md) compares identical
48-record output traces across off/v2/v3 in 20 alternating-order blocks. Minimal
v3 receipts fall from about 30.6 KB to 10.2 KB; retained references fall 48→16,
with a configurable 128-record cap and eviction/reused-image checks. Timing is
noisy (v3 faster in 12/20 pairs), so no stable task acceleration claim. Filesystem
I/O is included, model transport and GUI execution are absent. V3 is unintegrated;
explicit eviction status and buffered persistence/stall tests are next gaps.

## Latest follow-up — actual assistant delivery provenance self-use

[Delivery provenance](../research/live_control/DELIVERY_PROVENANCE.md) adds stdout
flush receipts and caller-declared source delivery/observation to an experimental
entrypoint. Two actual xterm self-use tasks pass. V1 source-ID overwrite is retained;
v2 separates source_delivery_id and own delivery_id. Twelve exact frames and
negative reference controls pass. Flush is not model receipt/viewing; caller
provenance is not authority. Additional receipt files are about 12 KB/run. Ready
schema discovery, memory bounds and matched tracing overhead remain gaps; default
entrypoints and full qualification are unchanged.

## Latest follow-up — causal evidence graph from actual recovery

[Offline causal trace](../research/live_control/CAUSAL_TRACE.md) exports 66 nodes
and 31 explicit links from unchanged servo-recovery-02. Three automatically derived
terminal-to-command gaps match the earlier report; five injected inconsistent
references/deadlines are rejected. Model-viewed-image provenance and complete
key/release authority lineage remain missing. Preserve observed-before versus
caused-by distinctions. Next instrument actual delivery/decision boundaries and
measure overhead before speculative execution or a shared trace ABI promotion.

## Latest follow-up — bounded oracle and Issue #13–#15 intake

[Rectangle oracle](../research/live_control/RECTANGLE_ORACLE.md) independently
checks saved flat-rectangle fixtures: five historical cases and eleven negative
controls distinguish missing effects, collateral changes and unsupported input.
This is development-known scorer validation, with no new live performance claim.

New Issues #13–#15 were read including comments (none at this check). #13 proposes
dormant speculative futures with fresh ordinary admission; preparation grants no
authority. #14 proposes retained, prioritized interrupts with ACK distinct from
resolution; current presentation replay proves neither detection nor delivery
delay. #15 proposes explicit observation/decision/authority/effect lineage; use an
existing actual-assistant recovery cohort first, preserving unknown links rather
than inventing causality from timestamps. These are experiment candidates, not
implemented ABI guarantees. Next prioritize evidence lineage and event-loss tests
before promoting speculation or the optional compact projection. Hourly issue
monitoring remains active and quiet on unchanged state.

## Latest follow-up — local-review trace projection and Issue #11/#12 intake (2026-09-13)

[Local review projection](../research/live_control/LOCAL_REVIEW_PROJECTION.md) tests
presentation_v3 on identical source traces: recovery JSON 35,130→24,785 bytes,
manual guided output unchanged, terminal receipts/critical recorded events preserved.
This is development-known replay only, without live timing/token or detection/ACK
claims. No default entrypoint change. [Semantic/evidence status](SEMANTIC_EVIDENCE_STATUS.md)
maps new Issue #11/#12 vocabulary and benchmark-contract proposals to real gaps.
Next live projection/fresh-event tests and an explicit scorer contract; preserve
orthogonal domain coverage and do not upgrade familiar cases into held-out evidence.

## Latest follow-up — same-task receipt recovery pilot (2026-09-13)

[Receipt comparison](../research/live_control/RECOVERY_RECEIPT_COMPARISON.md) repeats
actual assistant recovery with identical normalized task steps and same fixture.
Both score 24 px; receipts allow direct image lookup and historical clock anchors.
Clock queries fall 5→1; acceptance-to-score is 97.400 s vs 35.873 s. This is one
sequential, familiar-task pair with changed workflow, not causal receipt speedup.
Local programs remain below 0.9 s while decision gaps are 7.7–11.1 s. JSON bytes
increase; tokens unmeasured. 31 frames/source/step/scoring checks pass. Next repeated
order-controlled comparisons and boundary telemetry; no global promotion.

## Latest follow-up — terminal receipt resolves current image without guessing (2026-09-13)

[Review receipt](../research/live_control/REVIEW_RECEIPT.md) adds candidate compact
presentation_v2 / interactive_v14. Terminals carry latest observation identity and
actual reused-image path, historical runtime timestamp and local outcome without
changing source logs or authority. Eight replayed terminals pass; actual assistant
xterm task uses sequence 6 → 003.png directly and scores successfully, with six exact
frames audited. No matched recovery speedup or clock/token saving established.
Next same-task receipt comparison and planner/tool endpoint profiling.

## Latest follow-up — assistant recovery succeeds, end-to-end path remains slow (2026-09-13)

[Actual recovery](../research/live_control/SERVO_RECOVERY.md): the assistant observes
a known false visual goal, notices unchanged GUI X coordinate, obtains fresh feedback
after the test environment removes its overlay, then reissues under a new lease.
Saved displacement reaches 24 px with y/size preserved. Four programs, five clock
commands; first acceptance to independent score is 97.4 s despite 0.4–0.8 s programs.
False terminal to recovery acceptance is 59.7 s. 16 frames/source/order/release/scoring
checks pass. This is controlled restoration, not automatic verifier or persistent
occlusion recovery. Next current-image addressing/endpoint telemetry and effect
evidence to address planner/tool overhead; patch identity remains unqualified.

## Latest follow-up — occlusion exposes false visual completion (2026-09-13)

[Occlusion report](../research/live_control/SERVO_OCCLUSION.md) adds private X11
same-surface overlays during Inkscape drag feedback. Session20 stops on partial,
hidden and replacement cases but also fails the large-object positive control.
Candidate session21 uses raw matching before trimmed fallback: normal 24 px move
passes, but replacement at the target yields local_goal_reached with zero actual
saved movement. 57 frames/source/release/saved-state checks verified. Both candidates
remain unqualified. Next effect-verification/recovery and temporal/action consistency;
do not mistake stricter stopping or pixel resemblance for successful application work.

## Latest follow-up — acquisition and tracking error policies separated (2026-09-13)

[Trimmed tracking study](../research/live_control/SERVO_TRIM.md) diagnoses small-object
appearance error separately from identity. Trimming alone still prefers a red
distractor. Candidate session20 keeps raw source uniqueness and trims the largest
10% tracking pixel residuals. Blue-distractor trials complete +12 px at original
and one shifted position; red duplicates are rejected before input. Earlier
over-rejecting session19 is retained. 36 exact frames/source/saved-state checks pass.
Red rejection is not recovery; dynamic identity/occlusion remains open. No CLI
promotion or speed claim. Next negative target-loss tests and planner recovery.

## Latest follow-up — real distractor breaks visual identity (2026-09-13)

[Distractor failure](../research/live_control/SERVO_DISTRACTOR.md): session17 tracks
a neighboring red rectangle and moves the held target -48 px for a +12 px goal.
Authority bounds hold but identity is wrong. Candidate session18 adds source-match
uniqueness screening and rejects this case before servo input; blue-distractor
small-object tracking remains unstable. 30 frames/source hashes/saved attributes
audited. Rejection is not task success; multi-object patch servo is unqualified.
Next temporal association/decoration sensitivity and recovery on fresh cases; retain
all prior single-object successes within their narrow scope.

## Latest follow-up — local callback stall classification (2026-09-13)

[Servo stall tests](../research/live_control/SERVO_STALL.md) compare four actual-app
output/cancel/expiry conditions on session_v16 and candidate session_v17. Both
release during blocked output and prevent late motion. v17 reports needs_decision,
expired or cancelled instead of generic failed after resumption. Two actual-app
goal/lost regressions also pass; 39 exact frames and source hashes audited. The
candidate is Python-harness only; interactive_v13 remains frozen on v16. Real
distractors, actual target disappearance and broader feedback/schema remain next.

Issue #6–#10 intake (2026-09-13): reactive macros/watch (#6) reinforce bounded
local effect control, but multi-surface/background authority is not implemented.
Adaptive views (#7) and composite packing (#8) remain optional matched presentation
experiments; retain plain overview, coordinate provenance and actual model-cost
accounting rather than image-count claims. Ephemeral learned control (#9) is an
optional accelerator track: first improve externally observable planner-latency
telemetry and deterministic baselines, then isolated shadow evaluation on fresh
cases before bounded real input. Learning cannot grant/extend authority; record
training cost, labels, retained data/weights and break-even reuse. Issue #10 adds
explicit planner-boundary / architecture / Python-implementation timing categories;
profile stable components before native probes, with differential semantic checks.
No immediate Rust rewrite or formal-proof project is inferred. These are research
menus, not a bundle to implement before evaluating the current correctness gaps.

## Latest follow-up — assistant-declared servo and explicit loss outcome (2026-09-13)

[Servo interface](../research/live_control/SERVO_INTERFACE.md) exposes candidate
session_v16/interactive_v13 pointer_servo with source patch/sequence, target and bounds.
Actual assistant image-based submission reaches 30 px with two local corrections,
zero remote pointer replies, preserved saved y/size and a 1.179 s local program.
This is a familiar layout and excludes planning/save/scoring; no speedup claim.
Actual-app selected-source loss now reports needs_decision instead of completed.
32 exact frames/source hashes/release outcomes audited. Ready advertises a partial
operation descriptor, not full JSON Schema. Next real distractors/loss, callback
stall tests, complete schema and cross-domain evaluation; no promotion.

## Latest follow-up — patch correction in actual Inkscape (2026-09-13)

[Patch servo integration](../research/live_control/PATCH_SERVO.md) connects a bounded
scripted patch policy through existing guided replies. Completed cohort 03 achieves
24 px movement from original and verified shifted positions with y/size preserved.
Selection-decoration tracking loss, ineffective coarse setup and an oversized setup
program rejection remain archived. 69 exact frames audited. Lost tracking currently
maps to finish/completed at the program level, so inspect controller outcome and
independent score. Deselection is a declared setup condition, not a robustness fix.
Next real distractors/loss, outcome/schema integration and actual assistant target
submission; no remote-model speedup or promotion.

## Latest follow-up — deterministic patch effect sensor (2026-09-13)

[Patch anchor feasibility](../research/live_control/VISUAL_ANCHOR.md) adds offline
NumPy patch search after the assistant reply timeout. Four generated movement,
duplicate and disappearance fixtures plus three boundary checks pass. Historical
Inkscape replay distinguishes zero object movement from 23 px movement; search-only
times were 25–65 ms. This is not fresh-app or integrated servo evidence. Next connect
planner-declared target/update bounds to owner admission, then test fresh positions
and distractors with independent effect/collateral scoring. No runtime promotion.

## Latest follow-up — actual assistant reply misses deadline (2026-09-13)

[Actual guided self-use](../research/live_control/GUIDED_SELF_USE.md) tested the
published candidate with assistant screenshot decisions. A correction arrived
13.391 s after yield, beyond the maximum 5 s reply window; independent release
and stale rejection worked, but saved-object scoring was false (no displacement).
Seven exact frames and source hashes audited. A launch-only stdin-EOF attempt and
two schema mistakes are retained; the incorrect documented point example is fixed.
Next prioritize self-describing schemas and an isolated planner-declared bounded
visual-effect experiment on fresh cases. The local scripted controller's success
does not transfer automatically to a remote assistant. Goal remains active.

## Latest follow-up — worker yield and guided correction (2026-09-13)

[Guided pointer pilot](../research/live_control/GUIDED_POINTER.md) connects
session_v15/owner_v9 to one bounded reply during the original pointer hold, exposed
through candidate interactive_v12. No preplanned tail competes with correction.
Three known-fixture scripted Inkscape runs achieved 23 px for a requested 24 px,
within declared ±1 px. Audit verifies 39 exact frames and release/cleanup evidence.
Reply timeout and original expiry release despite blocked output; a consumed-reply
worker stall also releases and rejects late movement. That case still reports
`failed`, followed by successful observe recovery. Remote assistant use, fresh
cases and matched performance remain next; no baseline promotion or freeze credit.

Hourly Issue monitoring is configured for Unjuno/agent-interface. New Issues and
comments inform ongoing research; unchanged state stays quiet. Issue #2/#3 priorities
remain relevant feedback/continuation and separately evaluated selectable grids.

Issue #4, `Build the computer interface frontier models deserve`, and Issue #5,
`Explore agent-native visual addressing and feedback contracts`, were read in full
at publication (no comments). Treat #4 as the design thesis and #5 as an experiment
menu, not a bundled implementation mandate. Prioritize actual assistant use of
the continuation candidate, then isolated observation-bound addressing/effect
feedback experiments with fresh-case correctness and planner-boundary measurements.
Keep universal GUI fallback and independent scoring; deterministic fixture tracking
does not establish a general visual anchor or servo implementation.

## Latest follow-up — same-hold continuation admission (2026-09-13)

[Continuation admission](../research/live_control/CONTINUATION_ADMISSION.md) adds
candidate owner_v8 identity/revision checks and `continue_move` on the original
pointer-only hold. No button re-press, deadline extension or target rebinding.
Two controlled X11 cohorts passed 11/12 checks, including concurrent duplicate
replies (one admission), obsolete owner IDs, post-release/expiry/cancel rejection,
external physical release and focus/geometry boundaries.

This is the owner component only. No executor path replacement or planner-facing
continuation yet; do not run a correction alongside an unmodified preplanned tail.
Next integrate explicit yield/one response and sequence/age/update-count limits,
then real-app/assistant feedback correction. Issue #2/#3 were checked unchanged;
their priorities remain task-relevant feedback and fewer planner boundaries, with
selectable grids a separate matched presentation experiment. No speed claim.

## Latest follow-up — historical input-state bracketing (2026-09-13)

[Input-state report](../research/live_control/INPUT_STATE.md) adds candidate
owner_v7/session_v13. Observations include owner state samples before capture and
after image preparation: revision, owned input, physical pointer sample, focus,
lease deadline/time validity and timestamps. No lease renewal or atomic-state claim.

Four actual-app scripted cases passed: normal checkpoint, cancel/expiry during a
blocked capture wrapper, and cancel during blocked delivery. The last deliberately
shows unchanged held-state samples arriving after independent release. Ten exact
images and eight owner focus-boundary regressions passed audit. Existing entrypoints
are unchanged. Next define owner identity and bounded continuation admission;
never treat historical state as permission to revive input. No overhead/token or
live assistant replanning improvement measured yet.

## Latest follow-up — same-client pointer focus (2026-09-13)

[Pointer focus investigation](../research/live_control/POINTER_FOCUS.md) reproduced
expected-child/actual-parent focus (6291464 → 6291463) within Inkscape in cohort 08.
Candidate owner_v6 allows pointer focus within the original still-active client,
retaining geometry/hit-surface checks. Keyboard and mixed held keys remain exact
focus; the original lease fields are not rewritten. Session_v12 initializes this
owner directly; established entrypoints are unchanged.

Eight controlled boundary checks and three rapid-gesture Inkscape integration
runs passed, including blocked-output cancel/expiry release and absent tail motion.
The prior spaced diagnostic runs 06/07 also passed, while 08 remains a failure.
The new repeatable `audit_drag_focus.py` verifies 11 cohorts/131 exact images and
preserves the historical audit report. This is candidate core churn, not promotion.
Next: cross-app regression, explicit stale-feedback/release ordering, bounded
continuation and actual assistant in-flight feedback use. Precision and the
hand-made-window startup failure remain separate unresolved problems.

## Latest follow-up — bounded intermediate drag feedback (2026-09-13)

[Drag feedback study](../research/live_control/DRAG_FEEDBACK.md) adds candidate
session_v10/v11 with up to four intermediate observations and optional bounded
pre-capture delay. Same original lease and independent owner; no path replacement
or actual-assistant in-flight replanning yet. Existing entrypoints stay on v9.

Five Inkscape integration cohorts retained: 01 and instrumented 05 pass their
checks; 02–04 stop partially on focus changes. Blocked-output cancel/expiry tests
verify independent release and no tail motion. Immediate images missed object
movement; a 60 ms delayed capture in 05 showed movement before drag completion.
This does not establish paint readiness. Spacing gestures did not fix focus stops;
diagnostic instrumentation did not reproduce them. Fifty-eight exact images and
all owned-process cleanup/release records were audited. Next resolve explicit
freshness/release ordering and investigate focus before bounded continuation.

## Latest follow-up — desktop pointer transfer/precision (2026-09-13)

[Desktop pointer report](../research/live_control/DESKTOP_POINTER.md): candidate
entrypoint `interactive_v11.py` uses unchanged session_v9 with existing desktop
fixtures. One assistant Inkscape select/drag/save passed the narrow legacy SVG
score, but moved only ~12 px for a 24 px cursor path. One malformed chord program
was rejected before input and is retained. The API needs discoverable field names.

Two scripted pairs, in reversed order, confirmed that three-point paths moved
12/12 px and 25-point paths moved 20/19 px for the same 24 px request. All four
legacy scores passed; all four ±1 px precision checks failed. More samples alone
are not a fix. Fifty-three exact images, source/record consistency and releases
were audited. Task-level feedback during bounded manipulation is the next design
gate; the hand-made GUI startup issue remains unresolved. No runtime promotion.

## Latest follow-up — guarded placement negative/positive (2026-09-13)

[Guarded placement study](../research/openttd_task/GUARDED_PLACEMENT.md) found that
replaying the prior coordinates adds an unwanted road at tile 681: old score
passes, new 42-tile road/owner preservation score fails. This is a new replay,
not a retrospective surrounding-state measurement of the original episode.

A fresh assistant episode previewed the C selection outline and corrected the
drag endpoint; both target and surrounding-preservation checks passed. Thirteen
exact images across the negative replay and visual positive, matching initial
neighborhoods, source/save hashes, release and process cleanup were audited.
The visual development episode used two programs, seven frames and 43.42 seconds
including tool/reasoning delays. No speed comparison or held-out skill claim.

The shared backend is unchanged. Scoring covers roads/ownership in a bounded
neighborhood, not every side effect or the whole world. Fresh cases, wider desktop
regressions, hand-made GUI startup and continuous feedback remain open gates.

## Latest follow-up — shared pointer and OpenTTD self-use (2026-09-13)

[Shared pointer backend](../research/live_control/POINTER_BACKEND.md) now binds
observed surface/geometry once per program and validates bounded pointer steps
through the existing executor. The candidate is `session_v9.py`; pinned v10 is
unchanged. One managed-window cohort passed ten integration checks, but three
other fixture starts timed out; the setup fault remains unresolved.

[OpenTTD visual self-use](../research/openttd_task/SELF_USE.md) then passed the
independent target-road/connection/forbidden-row score through the same backend.
Three programs and fifteen exact frames are archived. This one known-task pilot
took 63.51 seconds from initial capture to final program terminal, including
assistant/tool delays; no human-speed or improvement claim. Cleanup and unchanged
canonical save were verified. The scorer does not constrain outside-region edits.

Full-frame quiet timed out in the animated scene (nine samples, 1222.8 ms), adding
cross-domain evidence for task-relevant feedback design. Next resolve fixture
reproduction, strengthen placement coverage, run fresh/desktop regressions, and
define observation-age/continuous-pointer feedback before promotion. Domain
Coverage Matrix and the OpenTTD → fixed-state Mindustry shortlist remain in force.


## Latest follow-up — pointer geometry/lifecycle (2026-09-13)

[Geometry and lifecycle report](../research/live_control/POINTER_LIFECYCLE.md)
advances the unintegrated owner candidate to `input_owner_v5.py`. Pointer leases
now require observed client geometry and reject movement/resizing/destruction.
The owner exposes termination and bounded two-second caller watchdogs; timed-out
owners reject retries and do not replay queued movement after a tested server
pause. Unexpected thread exit attempts release and records failed verification.

Sixteen private-X11 checks passed. Two additional fault cases covered a paused
and a terminated private Xvfb: pause/resume verified release and no queued move;
termination made release unverifiable, correctly recorded as failure rather than
success. The failed v4 BadDrawable cohort and its partial logs are retained.
The corrected release checks match their exact lease, not earlier release events.

Next bind surface/geometry to snapshot sequence in a new shared backend, add
whole-program pointer validation/cleanup, and run actual-app regressions plus
OpenTTD self-use. Existing v10 stays unchanged. Watchdog errors do not prove
resource cleanup while an X server is stalled; the supervisor must resolve the
old owner before any replacement can resume input. No speed/qualification claim.


## Latest follow-up — pointer owner candidate (2026-09-13)

[Pointer owner candidate](../research/live_control/POINTER_OWNER.md) adds absolute
motion, held buttons 1-3 and bounded vertical wheel pulses to a new independent
owner, `input_owner_v3.py`. Two private real-X11 runs completed 11/12 checks:
input delivery, expiry/cancel rejection, other-surface/wrong-focus rejection,
independent button release on deadline/cancel/focus/overlay, old-lease isolation
and keyboard keymap regression. Source/result/release logs are preserved.

This is not integrated into the shared backend or OpenTTD and is not a promoted
runtime. The v10 baseline stays unchanged. Geometry binding, destroyed surfaces,
X11 disconnect/owner-thread failure (synchronous waits can strand callers),
whole-program validation and actual-app regressions remain gates before use.
The added core semantics are architecture churn, not freeze convergence. Next
resolve those ownership/context lifecycle gaps, then connect the saved OpenTTD
fixture for actual pointer self-use. No speed, token or task-success claim yet.


## Latest follow-up — visible saved OpenTTD task (2026-09-13)

[Saved task and observer](../research/openttd_task/README.md) now provide a visible
A-to-C road placement fixture, a forbidden X row, and an observer-only script.
The canonical save is `research/openttd_task/results/cohort-03/baseline.sav`.
Two fresh process/profile/X11 restores preserve the declared six tile states
and two edges; both source screenshots show the task. An unsaved observer start
is rejected. The source save hash stays unchanged. Nine launches include an
initial save-suffix failure and a working but visually offscreen intermediate
fixture; those records remain available.

Setup and observer packages share a GameScript identity to load saved metadata,
but have separately pinned entry points. Only setup places signs. Never load
this save with the setup package during agent evaluation. Use the observer, and
keep fixture console operations out of agent task accounting. The six-tile
scorer is not a full-map damage check; repeated crash reset is still untested.
Next implement/verify the shared pointer/button/drag/wheel path with ownership,
focus/deadline/cancel/release invariants and use this fixture in actual assistant
operation. No performance improvement or benchmark qualification is claimed.


## Latest follow-up — OpenTTD placement scorer (2026-09-13)

[Oracle calibration](../research/openttd_oracle/README.md) advances the selected
OpenTTD pilot. Two seeds produced actual empty/partial/complete/extra-placement
states. The independent Python scorer accepts only complete, checking company
ownership, bidirectional adjacency and a declared forbidden row. Eight stage
observations are two episodes, not eight independent tasks. Three synthetic
counterfactual controls also reject wrong required owner, disconnected evidence
and missing tiles. Six failed setup attempts are preserved separately.

This is engine-API fixture construction, not assistant gameplay. The count-only
feasibility check is insufficient for the new placement contract: the actual
extra-placement state still has all required roads. Next split setup from a
read-only observer, freeze a visible task/save and verify restore/reset before
shared pointer input and assistant use. Goal revision 3 and Phase A remain active;
no runtime promotion or freeze qualification follows from this calibration.


## Latest handoff — Domain Coverage Matrix / Linux feasibility (2026-09-13)

The user's latest direction supersedes a DOOM-centric next-experiment priority.
[Current goal revision 3](CURRENT_GOAL.md) keeps the final live computer-use goal
and Phase A active. DOOM is one fast continuous motor/reaction stress domain,
not a strongest-benchmark proxy. Linux/X11 is the scope; do not expand candidates
for Windows/macOS yet.

[Domain discovery report](../research/benchmark_discovery/README.md) records
20 exploratory launch attempts, including setup failures. Current Mindustry
v160.2, OpenTTD 13.4/OpenGFX 7.1 and Luanti 5.17.0 rendered real game scenes in
private Xvfb. The old Ubuntu Minetest 5.6.1 font crash is separate evidence.

- OpenTTD: two seeded 64x64 initial height/owner/road traces match; independent
  negative road-count oracle works. It required SIGKILL after a 10-second
  SIGTERM wait. Short dense-GUI/placement pilot is the next candidate.
- Mindustry: two Fork loads differ at 10,817 of 75,000 tiles. Initial copper/core
  agree, but map name does not fix the loaded world. Tile rotation is unmeasured
  in this prototype oracle. Keep as the real-time planning candidate, gated on
  controlled small map/save and resource/rotation scoring.
- Luanti: authored small pad, fixed pose and independent zero-node score work
  with clean shutdown. Final fixture uses zero gravity; navigation is not tested.
  Retain as the 3D candidate, not a formal benchmark or public demo yet.

Five-second main-process samples under software rendering: OpenTTD 1.8% of one
CPU / about 197 MiB RSS; Mindustry about 718-730% / 913-915 MiB; Luanti about
187-208% / 203-217 MiB. Different workloads and setup/oracle overhead mean these
are feasibility warnings, not normalized rankings or shared-runtime performance.
Hardware GPU use and actual frame rate were not measured.

Next: preregister a small OpenTTD placement/GUI task and independent positive,
negative and near-miss scorer controls; establish restore/restart checks. Design
shared pointer/button/drag/wheel and mode/context binding from the missing axes,
while retaining DOOM and desktop correctness regressions. Do not bypass missing
shared actions with gameplay engine APIs. Mindustry fixed-state and renderer
budget gates precede its real-time planning pilot. Existing image-presentation,
critical-event and bundle/frontier evidence gaps remain open. No new runtime
semantics were introduced and no qualifying freeze revision was earned here.


This is the entry point for discussion in another chat. The user has authorized
direct updates to `main` when validated progress is ready. Keep successes,
failures, reproducible code and remaining limitations together in each update.

## Latest paired pilot and diagnosis correction

[Feedback pilot](../research/doom/FEEDBACK_PILOT.md) completed four AB/BA trials
on two matched seeds: combined2/2 complete, separate1/2, with a rejected expired
shot and aborted recovery retained. All28 frames and delivery audit. No general
speedup claim. Important: the apparently black recovery image and the older
shared-assistant-01/002.png contain normal scene pixels; original-detail rereads
show them correctly and the older PNG matches its published Git bytes. Thus
engine black-screen failure was not established. Next verify saved PNG through
encoded tool image and model-visible presentation, then resume timing studies.

## Latest timing evidence

[Traced combined feedback](../research/doom/TRACED_CLIENT.md) records local pipe
receipt and emits the image in the action call. Actual aiming/firing succeeds
(8 exact frames, all delivery/cleanup verified). Acceptance gap12.384s; combined
call bodies1.960/2.175s; first image-tool return to next call body10.444s. The
latter includes infrastructure/model/orchestration, not pure reasoning time.
Different cases prevent a speedup claim. Next: a matched, counterbalanced
combined-versus-separate feedback study with explicit missing outer endpoints.

## Latest boundary experiment

[Observation deadlines](../research/doom/OBSERVATION_DEADLINE.md) let the assistant
complete another basic-room task without clock requests (11 exact frames, 2
programs, all cleanup verified). Deadlines are fixed at latest capture +25 s;
this is a generous exploratory budget, not general real-time freshness. The
second operation gap still took 22.347 s. No speed promotion: next instrument
image-ready/tool-return/model-decision boundaries and reduce unnecessary result
retrieval calls. Unchanged runtime v7; final human-tempo goal remains active.

## Latest fix and actual self-use

[DOOM bindings fix](../research/doom/BINDINGS_FIX.md): correct arrow names resolve
directional nonresponse. Four fresh direction cases and actual assistant aiming/
firing pass; the latter completes the basic room with player alive (9 exact
frames, 2 programs). Use normal session_v7.py for new trials. Core runtime is
unchanged. About 20-second planner/tool gaps and the earlier black-screen root
cause remain open; there is no human-tempo or freeze claim.

## Latest response diagnosis

[Response diagnostics](../research/doom/RESPONSE_DIAGNOSTIC.md): one scripted
Space hold consumed one round and completed the basic scenario with player alive.
Three directional-input probes retained angle 0; per-image engine refresh and
delta-button availability did not resolve it. All 43 frames and cleanup audited.
The black-screen root cause and directional response remain open. Next: positive
control for keyboard binding and engine response, then fresh assistant gameplay.
No diagnostic candidate was promoted.

## Latest self-use evidence

[Shared DOOM self-use](../research/doom/SHARED_SELF_USE.md) failed: the assistant
encountered persistent black output and stopped with the episode unfinished.
Five frames and cleanup audited; a fresh scripted gap pair added eight frames
but did not reproduce black output. Both short-turn world crops were unchanged.
Next priority is separating game input response from rendering freshness, before
claiming shared DOOM task correctness. No performance or freeze claim follows.

## Latest implementation evidence

[Shared DOOM adapter](../research/doom/SHARED_RUNTIME.md) now uses the pinned
common backend/executor with full output. Three scripted readiness cases passed
(ordinary, cancel, expiry), ten frames reconstructed exactly, all terminal
releases and owner closes verified. Two failed adapter/harness cohorts are kept.
No game was completed in these probes. Next: actual assistant use of this adapter,
then remaining shared stress/continuous tracking coverage and qualification.

## Latest criteria revision

The user's Research Freeze Criteria Revision Proposal is adopted in
[CURRENT_GOAL revision 2](CURRENT_GOAL.md) and
[freeze criteria](../research/evolution/freeze_criteria.md). A 10% individual gain
is a strong promotion signal, not the threshold for ending architecture discovery.
Retain worthwhile smaller candidates and measure actual bundles, their interactions
and complexity/portability tradeoffs. Freeze requires small remaining meaningful
Pareto frontier movement plus failure/regression/churn convergence and hard
cross-domain correctness. Unknown bundle gains cannot establish saturation.

The [bundle contract](../research/evolution/BUNDLE_EVALUATION.md) fixes units,
provenance and study/stopping rules. The register has no measured rows yet;
historical ledger additions remain blank. This criteria update changes no runtime
and establishes no performance gain. Shared DOOM/tracking coverage and statistical
qualification remain open; no revision qualifies for freeze.

## Objective

**Updated working objective:** [CURRENT_GOAL.md](CURRENT_GOAL.md) adopts the
user's convergence/freeze proposal. Prioritize the evolution ledger, failure
taxonomy audit and shared evaluation plan before further local feature additions.
The final human-tempo objective remains. Research Freeze ends architecture
discovery only; the overall goal remains active. App goal text cannot be edited
with the currently available goal tool, so this document governs working scope.

Let the assistant itself operate a changing screen at an ordinary human-like
tempo. Optimize the full observation–decision–action loop, including unnecessary
model/tool boundaries, waiting, input/observation representation and actual token
cost. Preserve task correctness and information needed for decisions. Human-like
performance, real token savings and production readiness are not established.

DOOM is a later real-time evaluation and Product Hunt demonstration milestone:
the game must continue at normal speed while the assistant reasons. It does not
replace desktop task correctness. See [roadmap](../ROADMAP.md).

## Evidence ready for discussion

The [common active-input stress cohort](../research/evolution/STRESS.md) now
checks cancellation and expiry while Control is held across the four apps.
All eight interruptions stopped the text tail, then fresh intents completed
the saved tasks; 90 frames and all release records audited. This is scripted
functional evidence, not model latency or a qualifying freeze revision.
The [adapter inventory](../research/evolution/ADAPTER_DIFF.md) recommends bringing
DOOM onto the shared owner/lease/focus semantics before the more complex tracking
operation/event integration. Neither port is implemented by that inventory.

The [shared-runtime readiness smoke](../research/evolution/READINESS.md) now runs
the same pinned candidate across XTerm, Chromium, Calc and Inkscape keyboard
nudging. Eight declared cases passed saved-task checks; four expired requests
were rejected before input; 78 frames audited exactly. This is scripted harness
readiness, separate from actual assistant performance and freeze qualification.
Continuous/DOOM adapters and broader shared stress remain open.

Convergence indexing now covers seven recent revision groups and eight actual
assistant tasks (7 success / 1 failure). A separate register indexes nine selected
failure occurrences in four classes, including baseline controls and the known
focus/recovery regression. Ten charts preserve missing evidence as gaps or
not-measured panels; they do not establish convergence. See the
[evolution index](../research/evolution/README.md) and
[shared evaluation preparation](../research/evolution/evaluation_plan.md).

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

## Recovery after ambiguous focus

The [recovery follow-up](../research/live_control/RECOVERY.md) now separates
observe-only execution from focus binding in `interactive_v8.py`. Four controlled
episodes show the previous backend blocking recovery and both candidate episodes
recovering; an observation cannot grant input authority to its own program's
tail. Ten packet frames audited exactly.

Actual assistant use in Calc encountered a natural focus mismatch while closing
the save-format dialog, recovered by observation, and independently saved correct
A1/A2 values. Nine frames and four program releases audited successfully. The
first dialog image was not fully painted, requiring an extra observation.
Reducing these not-yet-useful observations and planner round trips is the next
performance problem; focus consistency alone is not paint or save completion.

## Pixel-quiet observation trial

The [pixel-quiet follow-up](../research/live_control/PIXEL_QUIET.md) adds an explicit
bounded `settle` step in `interactive_v9.py`. In actual assistant Calc use,
settling after Ctrl+S and after confirmation returned usable final images after
165/342 ms of local observation. Saved A1/A2 values were independently correct;
15 frames and both program releases audited. Six targeted tests passed.

The trial used two programs versus four in the preceding different-seed trial,
but this is not a matched causal comparison. It captured/emitted more frames.
Static loading screens also satisfy quietness; animation may never satisfy it.
Both counterexamples constrain its use. Next work is matched planner evaluation
and compact feedback delivery, not treating quietness as semantic readiness.

## Compact presentation pilot

The [presentation pilot](../research/live_control/PRESENTATION.md) adds optional
compact output to `interactive_v10.py`, retaining full local events and frames.
Two actual assistant Calc sessions used the same seed, runtime and action
programs; both saved correct values, with 29 exact frames across the pair.
Same-trace JSON output selection reduced bytes 36.39%/38.96%; replay of the prior
trial reduced 39.07%. These are byte counts, not actual model tokens.

The live pair is exploratory and ordered, with differing tool truncation limits;
its 19.43/28.51 s acceptance-to-evaluation intervals are not causal speed evidence.
Both required two programs. Compact mode preserves structural focus changes but
can omit transient visual-only warnings during settle. Full remains the default
until critical-event retention and stronger measurement are integrated.

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
