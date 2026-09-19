# Integration priority — 2026-09-19

**Agent-first clarification:** the primary user is the agent itself. Drive this
task by actual assistant use: observe a difficulty, improve the interface, then
use the same path again. Research supplies evidence for design choices. Prioritize
fewer avoidable tool boundaries, usable observations/results and recovery in the
agent's own loop. The [receipt self-use example](../runtime/results/receipt-self-use-01/README.md)
records the first concrete result-presentation improvement from this loop.
The [composed exchange](../research/live_control/AGENT_EXCHANGE.md) now removes
manual clock-request and steps-file assembly in that research path. Actual
assistant use covered a viewed draft followed by correction and independent
scoring, with the first rejected development attempt retained. This does not
yet connect the golden semantic compiler to the native CLI.
Its [review companion](../runtime/results/composed-review-01/README.md) returns
the receipt and referenced image together, avoiding a separate host image read
and WSL path conversion. This is a verified presentation path on retained data;
live-tempo and model-token effects remain unmeasured.
The [live Calc use](../runtime/results/calc-live-review-01/README.md) now connects
these through `agent_exchange --review`. It passed independent saved-cell
evaluation, while exposing delayed dialog pixels and 18–25 second outer gaps.
Next address observation/result continuation and caller assembly; native input
speed alone does not explain the remaining tempo gap.
The [final-drain integration](../runtime/results/calc-final-drain-01/README.md)
now reads an already-available independent result once after early saved-effect
evidence. Actual Calc use returned evaluation in the action response; a missing
result remains pending. It removes one outer continuation turn in this example,
not a socket exchange or the remaining deliberation gaps.
An [existing settle-step recipe](../runtime/results/calc-settle-self-use-01/README.md)
also avoided the separate observe program in one actual Calc session. Keep this
opt-in at expected GUI transitions: it adds native captures and cannot certify
semantic completion. No runtime change or universal wait policy was introduced.

The user's current direction is to concentrate this task on integration while
other contributors continue benchmarks and experiments. Product Hunt publication
has already happened according to the user. The engineering objective is a
usable, coherent interface; launch ranking is not a runtime acceptance criterion.

This implements the sequencing of [Issue #57](https://github.com/Unjuno/agent-interface/issues/57).
The bounded admission-audit work in [PR #2014](https://github.com/Unjuno/agent-interface/pull/2014)
is finished. Integration starts now and does not wait for the full research backlog.

## Selected starting path

**Primary-assistant verification:** the existing
`integrated_efficiency_client_v1.RuntimeClient.execute_handles` route has now
been [used directly by the assistant](../runtime/results/guarded-method-self-use-01/README.md)
for all six tasks, with visual grounding and repair in this conversation and
no helper model. Task 4 refused the old target before pointer input; reminting
from the viewed changed layout enabled the remaining tasks. Independent scoring
confirmed six exact submissions and 43 programs verified empty release.
This is the guarded method, not the distinct compiled state-graph runtime.
Its intermediate target check is not a semantic text-effect check. Prioritize
an explicit bridge from this existing route to the public native interface,
retaining those boundaries, rather than introducing a parallel caller.

The native result seam exposed a concrete mismatch: native sessions return
`status: completed/refused/release_unverified`, while the initial golden adapter
only read golden boolean flags. The v2 adapter now preserves native completion,
refusal reasons and the complete dispatch response; missing application scoring
remains unknown. Tests exercise real core admission, X11 session and API cleanup
with an inert backend. This establishes result interoperability, not visual
guard interoperability or a new live performance result. The next bridge must
still preserve visual target checks immediately before native pointer admission;
copying a research alias to a native window ID is not sufficient.
The newly reviewed [Issue #2337](https://github.com/Unjuno/agent-interface/issues/2337)
requires that live bridge plus scored effects, fault handling, actual model usage
availability and a held-out second workflow. The issue is now closed on GitHub,
but this result repair and the earlier research-route self-use do not establish
completion of that live integration gate.
An [actual native-adapter self-use](../runtime/results/native-result-self-use-01/README.md)
now confirms the result seam on a private Tk desktop fixture: a stale program
emitted no input, and a fresh one saved exact text with verified release. The
first accepted run had no scored effect at teardown; the successor reads the
independent result with a two-second bound and no input retry. All setup and task
failures remain retained. This also exposes that native capture supplies only
image metadata/hash: the harness still needs a separate assistant-visible PNG.
Neither that observation seam nor visual-target revalidation is integrated yet.
The [native artifact successor](../runtime/results/native-artifact-self-use-01/README.md)
now adds opt-in PNG output from the same X11 capture as the returned observation
hash. The primary assistant used that initial image to operate the fixture.
Its action image was still pre-save while the later independent effect succeeded;
both are retained with their distinct identities. This closes the duplicate
capture requirement for a native observation, but late-render continuation and
visual-target admission remain open. No matched latency/token benefit is claimed.
The [read-only observation successor](../runtime/results/native-observe-self-use-01/README.md)
now connects delayed-render continuation to the public API without dispatching
input or changing focus. Actual assistant use retrieved the saved state through
that path. Its timing trigger still uses the fixture scorer, so general
application-effect detection and caller recovery policy remain open alongside
visual-target admission. The growing native path must next connect source
identity and guarded method reuse, rather than treat this single form as the
complete integration workload.
Before connecting a guard that can stop a native program, repair X11's exception
boundary: a mid-program exception previously discarded completed operations and
observations. Native execution failures now retain that prefix, the uncertain
failed operation, emissions and recovery-release evidence through the common
result adapter. A private-Xvfb test injects failure after a real button press,
confirms release and prevents following text/save operations. This establishes
the required failure path; it does not yet implement the visual guard itself.
An [experimental native handle bridge](../runtime/results/native-handle-bridge-01/README.md)
now reuses the existing scoped handle store over the promoted X11 session.
Two primary-assistant saves passed with fresh checks before movement and press;
a controlled focus change refused reuse with zero additional input. This is
the first live connection of those two components, not full route convergence:
six-task reuse/repair, source revisions, semantic tail-effect checks and the
capture-to-input race remain open. Keep it experimental while extending that
same adapter, rather than promoting this single-field result as acceptance.

The [six-task native bridge successor](../runtime/results/native-six-task-bridge-01/README.md)
now verifies cold/reuse/reuse/refusal/visual-repair/reuse/reuse on the existing
Chromium fixture, with six exact independent submissions and zero old-target
input at task 4. The first run exposed a native text bug on the advertised `-`
character; it is retained and the supported text is now resolved before emission.
Field/Save operations use the native guarded bridge; URL navigation still uses
the research keyboard driver. This mixed path does not close public-interface
or matched-model acceptance requirements. Next integrate navigation/text and
semantic completion/recovery while keeping this six-task workload.

Starting repository revision: `2d78394e4128d9274030dcc52cf0957be2eb312d`.
Use the existing [golden desktop v3 entry point](../runtime/golden-demo-v3.sh) and
its [retained six-task result](../runtime/GOLDEN_DESKTOP_DEMO_V3.md) as the first
end-to-end desktop route. The retained route already covers cold acquisition,
warm reuse, stale-layout refusal, repair and post-repair reuse. A successor must
retain that result and its sources as evidence rather than rewrite the old run.

The [unified native CLI/API](../runtime/cli_v1/README.md) is the mechanical runtime
entry point. Its admission and native sessions are useful integration surfaces,
but their existence alone does not connect the golden route's semantic compiler,
feedback, accounting and repair. That boundary needs an explicit adapter before
claiming one unified end-to-end runtime.

| Responsibility | Starting component | Integration requirement |
|---|---|---|
| Setup and diagnostics | `runtime/setup-golden-demo-v3.sh`, v3 doctor | Check the actual route's dependencies before spending a model call. |
| Model interaction and accounting | Existing golden v3 grounding adapter and shared caller | Preserve every attempted call and actual usage; keep provider coupling at the adapter boundary. |
| Representation and local continuation | Existing compiled desktop workflow | Intermediate evidence must influence continuation; retain cold/warm/repair accounting. |
| Native execution and admission | `runtime/cli_v1`, `selector_v1`, `core_v1`, selected backend | Preserve caller freshness, explicit target identity and release semantics; own and close resources. |
| Feedback and task result | Existing exact observations and independent desktop scorer | Expose concise results and retrievable evidence; distinguish program completion from task success. |
| Invalidations and recovery | Existing stale-layout refusal and bounded repair path | Retain completed effects, stop on uncertainty, and avoid blind replay. |

Start with Linux/X11 desktop integration. Existing Win32/Quartz work remains
available, while portability expansion, additional benchmark families and new
compression mechanisms stay outside this first integration increment. DOOM
remains a later continuous-control stress domain alongside desktop coverage.

## Delivery order and acceptance

The [native window-review successor](../runtime/results/native-window-review-02/README.md)
now carries Calc's dialog and parent-window review on one bridge connection.
Each explicit handoff invalidates old aliases/sources, advances binding revision,
and returns the exact image used by the next assistant decision. The live final
version saved [116,476] and refused both old-target probes without input. The
destroyed-dialog feedback error is retained, with a successful read-only review
of the parent alongside it. This replaces per-stage connection reconstruction;
it does not establish a matched latency benefit or public multi-client semantics.

The [Calc text conditions](../runtime/results/native-calc-text-01/README.md)
reproduce 116 becoming 16 in one of eight zero-gap inputs; all eight 2 ms and
eight 10 ms inputs matched. A shared research helper exposes explicit pacing
without changing the native default, and a fresh primary-assistant two-cell
task succeeded with 2 ms and no value repair. This small matrix does not establish
causality or a universally safe delay. Post-dialog observation handoff remains
the next integration gap exposed by the same Calc workflow.

The [Calc transfer](../runtime/results/native-calc-transfer-01/README.md) now uses
the same native handle/feedback path on an existing second-application task.
The primary assistant completed exact saved cells after a flat-target refusal,
format-dialog review and visual correction of a dropped repeated digit. This is
a recovered success, not clean transfer or broad held-out evaluation. Prioritize
the observed repeated-character loss and explicit observation handoff after a
dialog closes; the title cue itself remains insufficient for task scoring.

The [native feedback successor](../runtime/results/native-feedback-01/README.md)
now returns application title cues together with a consistent native image from
the existing bridge. The six-task run uses these cues for continuation; a live
wrong-value control completed input but observed rejection and stopped before
the next task. The initial legacy-title failure is retained. Cue matching never
sets task success; independent scoring remains separate. This closes the external
post-save title-poll seam, not general semantic feedback or durable-effect proof.

The [native navigation successor](../runtime/results/native-navigation-01/README.md)
now moves between all six fixture tasks through the public native dispatch API,
while reusing the existing guarded field/Save bridge. Both the first navigation
timeout after three saves and the corrected six-save run are retained. Explicit
100 ms transition waits accompanied the successful run; causality and general
reliability remain unproven. Next integrate meaningful application feedback and
recovery across this route, then verify an existing second desktop workflow.
The harness still owns separate API/bridge connections and is not a promoted
single public agent interface. No matched latency or model-cost benefit is claimed.

1. **Make the existing entry points dependable.** Verify setup/doctor/result
   behavior and fix resource ownership and error propagation at the public API.
   First repair: the one-shot API closes the backend connection it creates after
   completion, refusal or execution failure; close failure retains the execution
   result/error and produces a non-success response.
2. **Connect one desktop vertical slice.** Follow installation, observation,
   grounding, guarded operation, useful effect and recovery through the selected
   route. Reuse the existing caller/continuation implementation. Resolve each
   missing adapter on that path before bringing in more optional mechanisms.
3. **Run the integrated acceptance workload.** Carry the six-task cold/reuse/
   invalidation/repair/reuse structure into a separately identified successor.
   Map the #57 requirements below to executable checks before live allocation.
4. **Retain the result and make the route understandable to a new user.** Provide
   reproducible setup, a stable entry point, typed results and a clear recovery
   route. Assess end-to-end correctness, latency and token use on this assembled
   path. Extend to an existing second desktop domain after the first report.

| Requirement | Enforcement / verification |
|---|---|
| Validated model output | Existing schema preflight, separately accounted. |
| Fresh target after model wait | Existing dependency revalidation before input; changed-target negative case. |
| Bounded continuation and release | Core/backend admission plus terminal release evidence; error and cancellation cases. |
| Correct task effect | Independent exact submission/effect check, not only a completed program. |
| Honest failure and usage reporting | Keep partial effects, failed calls, unavailable usage and recovery costs. |
| Resource ownership | Public API completion/refusal/exception regression tests; backend close failure cannot report success. |
| Comparative benefit | Reuse #56/#57 matched model/task/environment design and all-attempt accounting. |

The lifecycle regression tests exercise the API boundary with test doubles;
they establish no new GUI behavior or speed improvement. The existing golden
result remains scoped to its retained host/task/allocation.

## Intake from parallel research

Review Issues and merged results for a concrete gap in the selected route.
Record the applicable evidence, source version, assumptions, integration point
and regression case before adoption. Prefer one useful component at a time.
An isolated PASS is a candidate for integration, not an integrated product claim.
Keep failed ideas and revisit them when a stated condition has changed.

This task's new experiments should resolve an identified integration or
correctness gap, or measure the assembled route. Independent discovery remains
with the ongoing research work. The overall human-tempo goal remains open.


## Issue intake: persistent release quarantine (2026-09-20)

Issue #2437 supplies an immediately relevant condition for the persistent native
path: an unverified release must block ordinary follow-up input. The
[native quarantine regression](../runtime/results/native-release-quarantine-01/README.md)
now connects that condition to X11RuntimeSession and the existing handle bridge.
A real held-button failure refuses follow-up dispatch before backend access;
window review cannot clear the latch. This does not complete the broader host,
compositor or recovery protocol requested by #2437. There is no automatic reset.

Other reviewed candidates remain staged: #2530's MotorState bridge has reported
infrastructure stops before dedicated tests, so it is not evidence for promotion;
#2499 needs an actual persistent mixed-app trace rather than a union of earlier
component runs; #2448 needs semantic/effect evidence beyond title cues. Preserve
those gates while integrating useful, testable conditions into the common path.


The existing result/image presenter now also accepts explicit native observations
and feedback rows. In [actual Calc use](../runtime/results/native-review-self-use-01/README.md),
the primary assistant saw three exact native frames and completed entry/save;
independent workbook values were [116,476]. This removes host path conversion and
a separate file-image read in presentation, while preserving the full native
result and missing-image failures. Decision submission/waiting remain separate;
no measured speed/token or total-turn reduction is established yet.


[Native exchange self-use](../runtime/results/native-exchange-self-use-01/README.md)
now joins submission, bounded waiting and exact-image presentation under the
existing agent_exchange CLI for the private Calc harness. A normal stage returned
the dialog in the same call; an intentional zero-wait stage resumed read-only
without another program, and explicit finish returned the independent [116,476]
score. Requests/replies use immutable slots and exact decision hashes. This closes
the manual polling/presentation boundary in this bounded harness, not a public
persistent transport or a matched speed/token result. Full response verbosity,
server lifecycle reconciliation and transfer to other workloads remain open.


The [native observation-reference trial](../runtime/results/native-compact-self-use-01/README.md)
adds optional exact deduplication to the existing presenter/exchange. Primary use
with new values [360,125] succeeded. Same-report expansion and image equality
passed; two reply text bodies shrank about 7-8%, but base64-inclusive transport
shrunk less than 1%. Keep opt-in: this is modest byte evidence, not actual model
usage or latency benefit. Cross-app transfer remains the larger outstanding step.


The [Inkscape native exchange transfer](../runtime/results/native-inkscape-transfer-01/README.md)
exposed a real cross-app mismatch: guarded focus reassigned GTK child focus to
its top-level window, invalidating its own source binding. The bridge now preserves
validated descendant focus using bounded X11 ancestry; exact focus identity and
ordinary target guards remain. The shared harness accepts --app inkscape and the
same exchange/review path completed one rightward shape move/save. Independent
SVG scoring found x 50 -> 84 with y/size unchanged. Uppercase-key refusal and
pre-fix focus failure remain retained. The action was keyboard nudge, not drag;
18 chords versus +34 SVG units is not an exact motor-delivery result.

The [Inkscape input-boundary comparison](../runtime/results/native-inkscape-boundaries-01/README.md)
keeps that precision failure and tests explicit waits at two distinct boundaries.
After-click 50 ms yielded exact saved geometry in 8/8 allocated cases versus 4/8
without it; a wait only before save was insufficient. Fresh primary use with an
unallocated count of seven saved x=64 as expected. Integrate the existing explicit
wait as a scoped usage recipe, without adding primitives or changing shared
defaults. Other versions/loads, minimum sufficient delay and semantic readiness
remain unmeasured. Newly inspected #2704 (crash replay) and #2706 (independent
formal receipt emission) are not closed by this result.

[Native owner loss](../runtime/results/native-owner-stop-01/README.md) exposed
a recovery-status gap: a saved action with a killed owner and no reply remained
pending on every read-only resume. The private Linux harness now records its
process incarnation; absent/replaced/terminal or unverifiable owners return
unknown_requires_external_reconciliation without granting replay or release
authority. A stopped live owner remains pending and committed replies take
precedence. Immutable publication also syncs its directory entry. Fresh actual
use, SIGKILL, independent saved SVG/input-state checks and duplicate refusal
exercise this boundary. This is preparation for #2704, not its formal crash
matrix or a restart/recovery protocol.

A [persistent Calc/Inkscape round trip](../runtime/results/native-mixed-app-01/README.md)
now uses one bridge through focus change, format dialog, return and additional
input. It exposed a compositional bug: returning to Inkscape adopted its 1x1
InputOnly focus child as the application surface. A bounded managed-ancestor
lookup fixes the read-only handoff while preserving exact child focus and alias
revocation. Fresh primary use saved both [324,455] and SVG x=62; all ten stale
target probes refused without input. The existing harness supports two-app
setup and an explicit stage budget, not a separate control route. #2499's full
three-app/four-transition controlled allocation remains open.
