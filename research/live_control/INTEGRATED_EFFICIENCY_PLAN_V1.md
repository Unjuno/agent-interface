# Integrated token-efficiency evaluation plan v1

Status: first formal allocation completed with frozen disposition RETAIN.

Implementation checkpoint: `integrated_efficiency_fixture_v1.py` now provides
the frozen A/A/A/B/B/B task shape, visibly distinct layouts and an append-only
exact-token oracle.  `integrated_efficiency_runtime_v1.py` and the interactive/
socket entries connect that fixture to the existing `session_v33` checked-input
path.  The positive, duplicate and wrong-token oracle controls pass offline.  The
formal controller and source manifest are implemented.  The preregistered live
result is reported in `INTEGRATED_EFFICIENCY_LIVE_V1.md`.

An engineering-only X11 smoke starts the adapted Chromium process, emits the
six declared tasks and an exact initial frame through the existing runtime, then
finishes cleanly.  With no task input, the independent oracle reports all six
tasks missing, zero records and `success:false`, as required.  This smoke makes
no model call and is not part of the future formal allocation.

`integrated_efficiency_protocol_v1.py` now enforces the exact arm/task/layout/
route schedule, complete per-call usage, image-backed planner-generation counts,
exact submissions, releases, and the persistent task-4 old-reference refusal
before repair.  It independently computes cumulative input tokens, generations,
observed break-even and the frozen disposition.  Positive, extra-model-call,
old-target-input, cross-task duplicate-call-ID, wrong-side-effect and no-gain
controls pass.  The first draft's task-local call-ID check missed cross-task
duplicates; that failure was found before commit and the validator now rejects
duplicates across the complete comparison.

The first two-layout socket probe exposed a pre-input constraint: query-string
characters in the task URL are outside the runtime's bounded text alphabet, so
the whole navigation program was rejected with zero button input.  That result is
retained as `integrated-efficiency-runtime-probe-01`.  The fixture now uses path
segments (`/task/1`); fresh probe-02 navigates layout A and B, captures distinct
exact frames, verifies four clean input releases, makes zero model/task-input
calls, and independently reports the deliberately absent six submissions.  Its
audit passes on Windows and WSL.

The engineering persistent-mechanics sequence required five preserved
allocations.  V1 used a vertically wrong human-inspected A point and its flat
patch refused before task input.  V2 reused A handles through three exact tasks
and reached the required task-4 `MISSING`, then the probe assumed a missing
record carried `sequence`.  V3 fixed that packaging error but the restyled B
field's taller interior made a 24x22 center patch flat.  V4 widened the fixed
field patch to 24x38 and independently completed all six tasks, but its report
looked for the wrong pointer event name and incorrectly counted admissions as
zero.  V5 fixes only that measurement: six exact-once submissions, four total
mints, A reuse on tasks 2/3, B reuse on tasks 5/6, task-4 old handle `MISSING`,
zero old-target pointer admission, 12 intended button-down admissions and 41/41
verified releases.  Windows/WSL audits pass.  These human-point runs validate
mechanics only and do not enter the three-arm efficiency comparison.

The first common-client three-arm mechanics run independently completes plain
6/6, then rejects ephemeral's hyphenated task-derived alias before target input;
persistent is not started.  This seventh pre-prereg discovery is an interface
mismatch.  The registry grammar remains strict; the client now normalizes and
bounds private alias prefixes.  Fresh v2 completes all 18 tasks exactly once.
Plain uses 0 mints/18 programs/36 durable calls, ephemeral 12/48/96, and
persistent 4/41/82.  Each arm records 12 intended button downs, every terminal
has empty verified release, and persistent's task-4 old handle is `MISSING` with
zero pointer admission.  The human-point, zero-model result validates that one
common client can express all arms; it is excluded from formal efficiency.

## Bounded integration-gap loop

Issue #57's 2026-09-14 follow-up makes integration-induced requirements part of
this milestone.  A failure on the composed path must be classified as one of:

- `existing_requirement_regression`;
- `interface_mismatch`;
- `integration_capability_gap` required for composed correctness, observability
  or bounded recovery;
- `benchmark_setup_accounting_defect`.

The authoritative pre-preregistration ledger is
`integrated_efficiency_discoveries_v1.json`.  It records the blocking
requirement, smallest repair, composed-path regression, status, allocation
effect and measured engineering overhead for each discovery.  Allocation totals
are explicitly non-additive when more than one defect shares a run.  The six
current discoveries are three interface mismatches and five benchmark/setup/
accounting defects; none demonstrates a regression in an established safety
requirement or a need for a new cross-cutting capability.

The first zero-model composed-runner probe completed all 18 GUI tasks but read
the exported submission history before it materialized at session finish, so its
provisional per-task accounting was zero and the protocol rejected the run.  The
failure is retained as orchestration-probe-01.  The runner now reconciles the
final append-only history back to its preserved task/source records by task ID.
Fresh orchestration-probe-02 passes: all three six-task sequences score exact
once, the task-4 old reference refuses before pointer input, all 14 synthetic
grounding invocations follow the frozen routes, and the protocol reaches RETAIN
under synthetic usage.  Both probes make zero actual model calls and remain
outside the formal comparison.

Only a defect that blocks this selected path, its correctness or its measurement
may add work here.  Prefer an adapter or shared invariant.  A new reusable
capability requires a falsifiable composed-path regression and must include its
own model/token/latency/runtime overhead.  If such a defect is discovered after
formal allocation begins and invalidates the experiment, the protocol returns
HOLD; repair/version the candidate and preregister a new finite block.  It may
not silently continue the same allocation or change its question or thresholds.

This plan is the first deliverable for Issue #57.  The preceding compiled GUI
mechanics block ended at live v5 with disposition
`ADVANCE_TO_MATCHED_EFFICIENCY_COMPARISON`.  This work therefore switches from
isolated primitives to one integrated path and one finite end-to-end comparison.

## Selected composition

| Responsibility | Selected component | Ownership in the integrated path |
|---|---|---|
| Model output compatibility | `schema_preflight_gate_v1` and the actual CLI structured-output path | Refuse incompatible planned schemas before starting GUI authority; account for fresh preflight calls separately and in cold acquisition. |
| Cold visual grounding | `compiled_form_grounding_v1` contract and Luna-low | Produce source-pixel field/submit points and one bounded method declaration. |
| Representation | `compiled_gui_interface_v1` plus point-derived scoped target handles | Retain method, predicates and evidence references. Symbols carry no input authority or raw steps. |
| Acquisition and accounting | `adaptive_acquisition_caller_v2` | Record every attempted/completed model stage, missing usage, skipped stages, phase timing, comparison class and typed partial execution. |
| Local execution | `compiled_gui_interface_v1` | Observe, select a declared branch, obtain fresh admission, act, verify the expected predicate and continue within fixed transition/time bounds. |
| Target identity and input | `target_handle_chromium_socket_v5`, `session_v33`, `InputOwner` path | Revalidate current pixels/binding immediately before consequential pointer input and verify empty release. |
| Feedback | compiled runtime receipt plus raw durable events/frames | Return completed prefix, typed outcome/reason, latest evidence and critical events; keep raw evidence retrievable outside normal planner context. |
| Task correctness | private HTTP submission history | Score the exact expected token independently from program completion and retain unexpected/duplicate submissions. |

The first comparison excludes hover acquisition, OpenTTD-specific detectors,
semantic-delta experiments, planner-evidence compression variants, local learned
controllers, a Rust rewrite and every unrelated optional feature.  They do not
block the chosen form workflow and would introduce extra experimental factors.
No provider-specific asynchronous inference or subagent is part of the path.

## Reference and candidate arms

The ordinary reference keeps its real batching capability.  The form is visible
in full before action, so the planner may return one bounded field-click, text,
submit-click program from one screenshot call.  It is not forced into one model
call per click.

| Arm | Per-task behavior | Persistence |
|---|---|---|
| A — plain visual program | One current full screenshot call returns source-pixel field and submit points; the checked runtime executes the complete bounded program and independently scores it. | None. Every task starts from current pixels. |
| B — current optimized, ephemeral | One current screenshot call produces the same grounding/method contract used by the integrated arm; scoped handles and local continuation execute the task. | The interface is discarded after each task. |
| C — integrated persistent | Cold behavior is identical to B. Subsequent equivalent tasks reuse the method and scoped references, with fresh local observations and admission but no grounding call while dependencies remain valid. | Retained until a dependency invalidates; only the affected grounding is repaired. |

This three-arm comparison measures whether persistence amortizes real grounding
cost without weakening the plain baseline.  It does not by itself attribute the
gain between symbolic representation and eliminated intermediate inference,
because the plain task can be batched from its initial screen.  If the main
result passes correctness, one separately labelled fixed-context diagnostic may
compare planner-selected versus local-selected intermediate branches.  That
diagnostic cannot determine the main RETAIN/HOLD/REJECT outcome.

## Finite workload

The new private fixture will keep one Chromium/X11 session alive and expose two
semantically equivalent layouts.  Layout A remains stable; layout B moves and
restyles the field and submit control so an old exact target dependency cannot
silently resolve.  The server logs an append-only submission history and knows
the presented task token but does not expose that history to the controller.

Each arm receives the same six-task sequence and token distribution:

1. cold task on layout A;
2. warm-equivalent task on layout A;
3. second warm-equivalent task on layout A;
4. task on layout B, which is the invalidation/repair phase for C;
5. post-repair warm-equivalent task on layout B;
6. second post-repair warm-equivalent task on layout B.

For A and B, layout B is an ordinary new current observation.  For C, the old
references must first stop with zero stale-target pointer admission, after which
one declared repair grounding call may replace the affected references and the
same task may continue.  No failed side effect is retried.  One setup failure may
end the arm and remains in the result; model or GUI task calls are never rerun.

The initial engineering allocation is one sequence per arm, in a frozen order
chosen before execution.  It yields no population success rate or tail latency.
The preregistration must freeze seeds/tokens, arm order, schemas, prompts,
attempt limits, layouts, hashes, timeouts, metrics and decision thresholds before
any model or GUI episode begins.

## Metrics and accounting

For each arm and task, record independent exact-token success, unexpected and
duplicate submissions, stale/wrong target pointer admissions, typed stop/failure,
fallback and repair outcome.  Count actual model attempts and completions,
requested model/effort, input/cached/cache-write/output/reasoning tokens, usage
missingness, model-visible images, planner generations, local observations,
durable calls, pointer admissions, releases and retained raw frames.

Use these timing endpoints:

- source observation to independently known task completion or typed stop;
- each admitted input acknowledgement to first useful feedback;
- model process wait, local execution, verification and repair separately;
- complete six-task elapsed time for each arm.

Cached input remains a subset of input tokens.  Context bytes are reported
separately and never substituted for tokens.  Monetary cost remains unavailable
unless a direct provider record supplies it.

Report cumulative tokens and planner boundaries after cold task and after each
of the five subsequent tasks.  The observed break-even point is the first common
task index where C's cumulative total falls below both A and B; if this never
occurs within six tasks, report no observed break-even.  Do not extrapolate an
unobserved break-even as a measured result.

## Requirement-to-test matrix

| Origin | Applicable requirement | Integrated enforcement | Regression/live evidence required |
|---|---|---|---|
| #52 / typed outcomes | Abstention or unavailable evidence cannot expose executable coordinates | Strict model validators, caller stop outcomes and zero-authority target result | Malformed/stop controls; layout invalidation has zero old-target admission |
| #53 | Every attempted call, early stop, skipped stage and repair is accounted | `adaptive_acquisition_caller_v2` attempt ledger and phase table | Existing 18-scenario audit plus reconciliation against every raw comparison call |
| #54 | Planned schemas must match the actual endpoint before GUI authority | Hash-pinned schema preflight before session creation | Fresh-or-cache result for every schema; rejected-schema control invokes GUI continuation zero times |
| #55 | Current target evidence after model wait is required before input | Read check followed by ordinary pointer-target revalidation/admission | Stable task input succeeds; changed layout refuses the old references before pointer down |
| Runtime invariants | Scope, focus, lease, cancellation, deadline, release and no blind replay | Existing durable submit/InputOwner path and bounded compiled runtime | Reuse only within exact declared session; all terminals release; fault controls stay closed |
| Effect/evidence | Program completion is not task success; completed prefix and raw evidence remain | Local predicate check, append-only independent HTTP scorer, raw event/frame hashes | Exact expected token once, no unexpected/duplicate token, raw artifact reconstruction |
| #12 / #46 | Comparison capabilities, endpoints and assistance must be explicit | Same fixture, model/settings, scorer, display, checked input and clocks | Plain batching retained; mismatches listed; complete per-phase timing and environment record |
| #56 | Intermediate local evidence must affect a later authorized action | Compiled method observes field effect and current Submit dependency before branch/action | B/C mechanics audit plus C live transitions with zero frontier-model resumption |
| #57 integration gaps | Composition failures need explicit provenance, smallest repair, regression and overhead; a formal-invalidating repair cannot continue silently | `integrated_efficiency_discoveries_v1.json` plus protocol-wide discovery validation | Six retained pre-prereg discoveries; missing provenance and silent formal-repair controls; invalidated formal trace returns HOLD |

## Frozen decision rule to place in preregistration

Correctness is a hard gate.  RETAIN requires all six C tasks to independently
submit exactly once, zero old-target pointer admissions during layout change,
successful bounded repair, verified releases and complete call accounting.
It also requires C to use fewer cumulative actual input tokens and fewer planner
generations than both A and B by task six, with an observed break-even no later
than task four.  Because the initial block has one sequence per arm, timing is
descriptive: C may not be called faster unless its complete six-task elapsed time
is lower than both references in this allocation.

HOLD applies when mechanics and correctness pass but accounting, comparability or
the single allocation is insufficient for the rule.  REJECT applies if C admits
an old target after invalidation, causes an incorrect/duplicate side effect,
cannot repair within the declared attempt, or fails to beat both references on
tokens and planner generations by task six.  A negative result ends the block;
it does not trigger another allocation with changed thresholds.

## Subsequent real-time DOOM gate

DOOM follows the integrated report rather than interrupting it.  Existing DOOM
work uses ViZDoom's small `basic.wad` scenario in `ASYNC_SPECTATOR` at nominal
35 tics/s and already verifies that game time advances during wall-clock waits.
That is useful real-time transport evidence, but it is not completion of a normal
game map.

The later public-demonstration study should load the packaged `freedoom2.wad`
base game directly, select `MAP01`, keep asynchronous 35-tic game time running
during model waits, use only screen/audio-visible information for decisions and
OS keyboard/mouse input for control, and score the actual map exit separately
from death or timeout.  It must record wall time, game tics, pause/menu state,
health/death, input holds/releases, model waits, observation latency and the full
episode video/evidence.  No pause, save-state stepping, API action injection,
automap/object/sector labels or privileged game variables may assist the
controller; game variables may be retained only by an isolated post-run scorer.

ViZDoom officially supports async player/spectator modes, direct base-game WAD
paths and map selection.  Its package includes Freedoom assets, so this gate can
be reproducible without redistributing commercial Doom data:

- <https://vizdoom.farama.org/main/api/python/doomGame/>
- <https://github.com/Farama-Foundation/ViZDoom/blob/main/examples/python/basic.py>
- <https://github.com/Farama-Foundation/ViZDoom>

This future gate keeps DOOM as a real-time motor/reaction benchmark within the
Domain Coverage Matrix.  It does not replace desktop, Mindustry or OpenTTD
coverage and no level-clear capability is claimed before the run.
