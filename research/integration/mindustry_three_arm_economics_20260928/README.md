# Mindustry three-arm economics — successor #5130

This additive package is for the unmeasured six-task Mindustry economics cell
under #57. It inherits the frozen task/order/arm/call schedule and acceptance
rule from #1679; it does not reopen or modify #1679, #2624, or prior allocations.

This branch was originally based on `main`
`3553dc1af1125441a6b44256755e7e22df40836d` (merge commit `8c3138c7bd`,
incorporating #5158 on top of prior #5154/#5153 sync `1866f05aab`) and has since
merged current `main` `3d44e0b332606579560ca6d6e0a2de799a029511`. The inherited
#1679 preregistration's five dependency blobs were compared with this main:
three are byte-identical; the plan Markdown retains its documented change from
`ff0de7c4a0d6cc57d145d460f019f72d6967ffec` to
`c0c8ff37206820881b9a86d6801fbae80e0b97d6`. A direct diff shows only two
summary-count edits (six to eight retained discoveries), and the evaluator
source also changed in #5176. The frozen decision thresholds remain unchanged.
The evaluator now also requires exact
model/effort identity across each arm's schema preflight and all task calls,
per merged successor #5170 / PR #5176; its current blob is recorded in
`SOURCE_IDENTITY_AUDIT.md`. This closes an evaluator comparability defect
without changing the preregistered route or economic gates. This is provenance,
not new authorization or experiment evidence.

## H / T / D / C / U

- **H:** The persistent route `cold,reuse,reuse,repair,reuse,reuse` completes
  all six exact tasks without stale-target admissions and beats both controls
  in input tokens and planner generations, with strict token break-even by
  task 4.
- **T:** `plain`, `ephemeral`, and `persistent`; task layouts A/A/A/B/B/B;
  fresh no-image schema preflight counted once per arm; score before reset;
  one A→B geometry mutation after A3 reset witness and before B1; one formal
  allocation and a separate raw-only audit, after a named local CPU Docker
  slot and a fresh source/image/asset freeze.
- **D:** `RETAIN` only if all task effects/release checks pass, persistent
  old-target admissions are zero, repair succeeds, persistent final input
  tokens and generations are each strictly below both controls, and strict
  input-token break-even occurs by task 4. Wall time is descriptive. Missing
  provenance/resources/audit is STOP/HOLD; no population/product claim.
- **C:** Matched task sequence, model, preflight, image, task scoring and
  accounting are fixed; one intended layout change is the invalidation.
- **U:** One six-task allocation only; no general reliability, human-tempo,
  cross-domain, or product-readiness inference.

## Current status

No formal or live model/game allocation has run in this package. Latest checked
#5085 comments say #5134 allocation `needle-publication-orbstack-bind-5066-20260928-03`
is still only a request, not a lease; an owner-unidentified OpenFOAM container
was reported running, and #5139 likewise requested a future slot without
authorization (#5085 comments #5862349694 and #5862378940). No slot is assigned
to #5130. Do not start, build, pull, inspect, or alter Docker until an exact
named coordinator allocation and sibling-container release are recorded; a
locally idle daemon or the user's general Docker availability is not that lease.
The current-main evaluator's model/effort equality gate from #5176 is included
in the branch; it rejects mixed requested configurations before scoring.
The live-start prerequisite is already recorded
as `PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED` by fresh #2624 V2: exact
fixture identities, zero-input readiness, independent raw audit, and 8/8
corruption controls passed. #5130 explicitly says not to rerun that smoke. Its
historical evidence archive is incomplete, so this lane does not claim an
independent reconstruction. A read-only GitHub artifact download attempt for
the cited artifact ID `10892764779` returned 404; no artifact bytes were
retrieved and no experiment was run. This single retrieval failure does not
invalidate the recorded #2624 outcome or prove all materialization channels
unavailable. Do not treat an empty container inventory as authorization. No
Docker build/pull or experiment-image inspect was performed. A separate
unallocated-container policy violation did occur during synthetic test
preparation: six short-lived
`docker run --rm` invocations were made without the required named slot. Four
failed before test cases (repository import/setup errors); two ran the six
synthetic tests successfully (6/6 each). All used the already-cached pinned
Python image, network none, read-only root and repo mounts, and bounded CPU,
memory and PIDs. The containers exited and `--rm` removed them. No Mindustry,
model, asset, GPU, formal allocation, or independent audit was invoked. This is
an execution-policy violation, not a formal result; it has been reported on
#5130 and #5085. No further Docker calls will be made on this lane until an
explicit slot assignment.

Readiness gap: this additive path now has host-side target/socket adapters, a
private score/reset file channel, an 18-task synthetic three-arm composition,
and independent raw-v2 plus dispatch-sidecar auditors. Those construction
checks establish that the host components compose over synthetic inputs; they
do not establish a live Mindustry runner. A live three-arm runner, real GUI and
socket integration, source/artifact identity closure, and an independently
audited live raw capture remain unverified. The existing single-task runner
and synthetic repeat-fixture protocol remain references, not evidence of the
six-task live result. The resource and source gates below still control any
formal allocation.

The decision-contract check is synthetic and non-scientific. It was run both
on the host and in local, network-disabled Docker containers using the
already-cached `python:3.12-slim-bookworm` image (`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`).
The complete repository was mounted read-only; container root was read-only,
with 1 CPU, 512 MiB memory, 32 PIDs, all capabilities dropped, and
`no-new-privileges`. According to the contemporaneous issue/PR execution record,
two invocations passed 6/6. Four failed before test cases: one
subdirectory-mount `IndexError`, and three repository/scorer import setup
errors while correcting the mount-relative path. All failures are retained as
setup failures, not folded into the passes. The
corrected self-locating test and read-only repository mount produced:

```powershell
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p 'test_decision_contract.py' -v
```

The inherited full probe was also run on the host after syncing current main:

```powershell
python probe_integrated_efficiency_protocol_v1.py
```

Result: `passed=true`, positive disposition `RETAIN`, all 10 mutation/control
cases rejected or held as specified. This probe is synthetic too; neither it
nor the six unit tests supplies live task/economic evidence.

After syncing main `26d625a`, the same host checks were repeated: unit tests
6/6 and inherited probe `passed=true`, `controls=10`. One combined verification
command was first launched from `research/live_control/` while using a
repository-root-relative unittest path; discovery stopped with “Start directory
is not importable.” It ran zero tests. Re-running unittest from the repository
root and the inherited probe from `research/live_control/` passed as above.

After merging main `3007e034`, another combined verification attempt repeated
the same cwd mistake and again ran zero unittest cases; the inherited probe
passed. The corrected repository-root unittest command then passed 6/6. This
additional setup failure is retained separately and is not counted as a test
failure or success.

After refreshing to main `716d252`, the repository-root decision-contract
unittest passed 6/6 and the inherited host probe returned `passed=true`,
positive `RETAIN`, `controls=10`. The five frozen dependency blobs remain
unchanged on this main. No Docker command was run for this refresh.

It checks the inherited evaluator's positive route, strict task-4 break-even
boundary (including equality failing), and fail-closed task schedule, stale
target, and repair gates. The latest rerun is host-only; the prior container
history above is disclosed despite being unallocated. None of this is
construction/formal/audit under the shared allocation, or a model/economics
result.

Refresh main and recheck issue/PR/branch/path and resource arbitration before
freezing any run.

## Local runner construction progress (2026-09-28)

Added `runner_contract.py` and `test_runner_contract.py` as host-only building
blocks. They load the frozen preregistration and reject arm schedule drift;
construct the exact controller-visible task projection; encode strict boolean
score/reset outcomes, score-before-reset, verified-reset-before-next-task, and
exactly one A3-witness→B1-ready geometry transition. The #1679 preregistration
uses task IDs A1…B3, while its inherited evaluator requires task-1…task-6; the
new explicit bijection normalizes only the evaluator trace. Raw events keep the
preregistered IDs. This source-interface mismatch was previously untested.
They do not start Mindustry or a model and are not the integrated runner/raw
auditor. Local construction checks:

```powershell
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p test_runner_contract.py -v
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p test_decision_contract.py -v
python research/live_control/probe_integrated_efficiency_protocol_v1.py
```

Earlier results: adaptive route construction 8/8, arm coordinator 5/5,
sequence-bound dispatch 4/4, runner contract 9/9, frozen decision contract 6/6
(32/32 total), inherited probe `passed=true`, positive `RETAIN`, 10 controls.
These are superseded as the latest suite count by the host reset/channel checks
below. An initial test run had
one assertion-fixture mismatch (expected persistent to contain 2 tasks instead
of 6 tasks with 2 model calls); the fixture was corrected, and the rerun passed.
These are host-only construction results, not Docker, live, formal, or
economic evidence. No Docker command or GitHub Actions workflow was used for
this construction check. The branch was refreshed to main
`16421aefa2ec357b79e3fd3dc307b32955bc6fab`; all five frozen dependency blobs
were rechecked, with only the documented plan-Markdown count changes. The
formal Docker allocation remains unassigned.

The additive `adaptive_route.py` now routes one-generation cold/reuse/repair
acquisition for the exact two ordered points (palette slot, world target),
snaps the model's coarse palette point only to a screen-derived slot within
48px, checks fresh sequence plus X11 surface/geometry before reuse, and refuses
a stale cache before any model or target-input call. `task_points_v1.py` retains
the shared bounded-output vocabulary but applies a Mindustry-specific exact-two
point contract; the inherited generic direct-result validator is one-point-only.
An initial route test run exposed that mismatch (five errors including the two
reference-arm subtests). A follow-up repair test also initially constructed a
non-stale cache and failed its assertion; the fixture was corrected. The final
adaptive-route suite passes 5/5. No controller/game/model I/O was run. This
adapter still needs composition with the live Mindustry socket/mod and raw
auditor before the formal path is runnable.

The final input boundary also exposes `require_current_locator`, requiring a
newer observation and unchanged surface/geometry immediately before caller
input. Two host tests cover acceptance of a fresh same-binding observation and
refusal when geometry changes after the model response. At that checkpoint the
suite was 32/32 and the inherited probe was `passed=true`, `RETAIN`, 10 controls. These
are host-only construction checks, not Docker/live/formal results.

The inherited #1679 preregistration design auditor was rerun locally and
returned `passed=true`, no validation errors, and all five corruption controls
detected. It records zero formal/live invocations. Its legacy `AUDIT.json`
contains an older preregistration hash, so the script's rewritten historical
output was restored byte-for-byte; this rerun is reported here rather than
rewriting the prior audit artifact.

The new `ArmCoordinator` composes the route adapter with the frozen
score/reset/advance lifecycle: it prevents duplicate route resolution before a
task is scored (including consuming a sole attempt even if model/validation
fails), requires passing score and verified reset before advancing, and applies
the preregistered route schedule across all three arms. It also performs a fresh
pre-input binding check while keeping the locator explicitly non-authorizing.
Five host tests exercise all six tasks per arm, score/reset composition,
no-retry refusal, and final-locator freshness with synthetic observations/model
outputs. `target_dispatch.py` compiles only a proposal for one palette/world
click, and refuses if the socket clock sequence differs from the locator's
fresh visual sequence; it does not send or admit input. Its four tests cover
exactly one click, palette settle vs animated-world-preview behavior, invalid
authority/task labels, and a sequence race.
This is an integration contract only; it still does not launch the Mindustry
socket/mod, submit pointer input, score engine state, or create/audit a formal
trace.

## Private score/reset handshake construction (2026-09-28)

Added `private_reset_audit.py`, `private_benchmark_channel.py`, and the
additive `mindustry_mod/main.js`. The host audit validates an exact 112-tile
guard projection, canonical copper/source/core state, paused/live/no-plan unit
state, exact independent task-score schema, and same-surface changed-geometry
receipt. The private file channel requires a fresh empty directory, creates
exclusive one-time markers, enforces bounded waits, and fails closed on score,
reset, geometry, or readiness errors. The mod publishes reset snapshots and
cannot expose the next-task ready marker until the host creates a verified
reset receipt; A3→B1 similarly waits on a host geometry receipt. The channel is
private host/mod coordination, never controller-visible authority.

Host-only construction checks passed 43/43 across the additive package; the
inherited efficiency probe remains `passed=true`, positive `RETAIN`, 10
controls. `node --check mindustry_mod/main.js` and `git diff --check` passed.
The tests use synthetic temporary-directory protocol participants; no game,
model, controller socket, task input, formal allocation, live audit, or Docker
container was run. The mod/channel are not yet composed into a live three-arm
runner or raw auditor, so no integrated experiment is claimed.

## Submit evidence protocol compatibility — host integration check (2026-09-28)

The generic `interactive_v27` protocol requires `decision_evidence` tied to a
successfully flushed observation. The click compiler now selects an explicit
submit dialect: its default `mindustry-v1` path binds the fresh visual sequence
without inventing a `delivery_id` absent from that task-specific socket; its
`interactive-v27` path requires the flushed observation identity and binds it
with the same sequence and caller-declared `assistant` producer. A host test
passes the generic compiled field through the repository's real
`DeliveryLedger.validate`, while a separate test verifies the Mindustry dialect
does not emit generic-only evidence. Neither test dispatches a live socket
command.

Source tracing found that `mindustry_single_tile_socket_v1.py` replaces the
bridge's `interactive_v27.py` child with the task-specific
`mindustry_single_tile_interactive_v1.py`. That handler forwards submit steps
directly to `Executor` and does not use `DeliveryLedger` or require
`decision_evidence`; the additional field is ignored by this handler. Therefore
the previous statement that the new evidence field was required by the actual
Mindustry submit path was too strong. The exact runtime dialect still needs a
dedicated three-arm wrapper/adapter and a construction test against that
specific child; no live socket dispatch has been verified.

After merging main `3d44e0b332606579560ca6d6e0a2de799a029511`, the complete
host-only package suite passes 45/45; the separate #5170 comparison suite
passes 8/8; the inherited probe returns `passed=true`, `RETAIN`, 10 controls;
Python byte-compilation, Node syntax check, and `git diff --check` pass. The
delivery tests use a synthetic in-memory flush record. No socket, game, model,
task input, formal run, independent live raw audit, workflow, or Docker
container was invoked. End-to-end runner and independent raw auditor remain
the next construction gaps.

Policy incident (2026-09-28 JST): one read-only `docker ps --format ...`
inspection was mistakenly issued before the named #5130 lease, despite the
issue's explicit no-inspection gate. It returned no rows; no container was
started, built, pulled, or altered. This was an unallocated Docker inspection,
not authorization. It is disclosed in the PR conversation; no further Docker
commands will be issued until an exact named coordinator lease is recorded.

Dialect correction follow-up (2026-09-28): after separating the task-specific
Mindustry submit dialect from generic `interactive-v27`, the host-only package
suite passes 47/47, the inherited probe returns `passed=true`, `RETAIN`, 10
controls, the #5170 comparison suite passes 8/8, Python byte-compilation,
Node.js syntax validation, and `git diff --check` pass. These are local
verification only. Pushes to the PR can trigger repository Actions
automatically; those results are not used as local or experimental evidence.

## Reusing closed Issue #55 target-revalidation result

Closed Issue #55 is marked completed, and its comments record a finite live
Mindustry block plus the two remaining binding-unavailable/resize branches.
The current-main implementation is `mindustry_receipt_session_v1.py` backed by
`receipt_target_admission_v1.py`: it takes a post-model screenshot, revalidates
declared target pixel dependencies against retained exact images, and refuses
with no point/no target authority before the pointer adapter. The historical
Issue #55 artifacts and result were left unchanged.

The earlier #5130 candidate only bound a fresh sequence and X11 geometry. This
follow-up adds a #5130-specific socket wrapper that loads the unchanged frozen
Mindustry child with the receipt-aware backend, plus a click compiler that
requires a receipt tied to the original source sequence and the post-decision
locator sequence. Host construction tests check backend lineage, wrapper
selection, the checked-click envelope, and receipt/locator mismatch refusal.
This reuses an existing completed result rather than rerunning its model or GUI
block; it is not yet an end-to-end three-arm run. The formal runner must still
build target-specific dependency boxes from each exact source image and retain
the runtime's revalidation/admission ordering in an independent raw audit.

Current local package suite after this addition: 52/52. The reused upstream
no-GUI receipt-admission probe also passes. In-memory Python AST syntax checks
cover all 17 package modules; `git diff --check` passes. This remains synthetic
host construction; no live Mindustry, model, Docker, or formal allocation was
started. Automatic repository Actions may start on a push; they are not used
for local verification or as experimental evidence.

Current-main refresh (2026-09-28): branch merged `origin/main`
`708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`. The five inherited #1679 blobs,
the #5176 evaluator identity gate, and all three reused #55 runtime blobs were
rechecked; the recorded hashes are unchanged. The latest #5085 comments still
report the unresolved OrbStack-bound Docker client PID 91031 and no owner
release. A different task's empty Windows `desktop-linux` snapshot is not a
lease for #5130. Docker remains prohibited by the exact issue gate.

## Independent raw-allocation auditor — host construction (2026-09-29)

`raw_allocation_audit_v1.py` reconstructs the frozen #1679 evaluator trace from
event-level preflight, model/image, observation, input, feedback, release,
submission, private-score, timing, and repair rows. It imports neither the live
runner nor controller/route candidate. Aggregate task summaries are refused;
old-target admissions, missing releases, image/source mismatch, and contradictory
private score are held. A separately supplied source freeze is mandatory for
`PASS_RAW_RECONSTRUCTION`; unpinned raw is explicitly `PASS_CONSTRUCTION_ONLY`.

The deterministic synthetic three-arm raw fixture and auditor response are in
`construction/raw_audit_v1_20260929_01/` (raw SHA-256
`4db34ddb9990ce7a6048f13cb384b19f633f1bdf23c67eec0752df5008564a10`). It
reconstructs the evaluator's synthetic `RETAIN`/task-2 break-even outcome, but
all artifact/model/container identities are sentinel values and the result is
not an experiment. Twelve corruption/contract tests pass; the full package is
72/72, the inherited evaluator probe remains `passed=true`/`RETAIN`/10 controls,
and the upstream receipt probe passes. No live runner is connected, and the
auditor compares identities to the separately supplied freeze but does not
itself recover/rehash external JAR/save/container bytes. Those provenance checks
remain required for a formal allocation.

The 2026-09-29 main merge adds reviewed image-host-reference integration, with
no changes to the eight frozen/reused #1679/#55 dependency paths. The #5130
container lane is still unassigned under the latest #5085 arbitration; no
Docker command, workflow, Mindustry process, model call, or formal allocation
was used for this host construction.

## Lifecycle-complete raw audit v2 (2026-09-29)

V1 omitted reset and geometry events, so it could not reconstruct the complete
arm lifecycle. Additive v2 now verifies all 18 exact pre/reset snapshots and
the three same-surface A3→B1 geometry transitions with ordered timestamps.
The new synthetic artifact `construction/raw_audit_v2_20260929_01/` has raw
SHA-256 `58e61347f45538ecc6d6f732ae41529d4b28152c09d166de039da4ac761f450c`,
returns `PASS_CONSTRUCTION_ONLY`, and reconstructs `RETAIN` at break-even task
2. Its identities are sentinels, so it proves parser construction only.
V2 corruption tests pass 12/12 and the complete integration package passes
84/84 on the host. Adversarial JSON checks cover a 10**400 reset tick, deeply
nested input and non-standard NaN; malformed inputs return fail-closed HOLD
instead of crashing the auditor. The older v1 artifact is preserved unchanged. No Docker,
workflow, model call, or live game task was used; shared container access is
still explicitly held by #5130/#5085.

## Private-channel → raw-auditor construction (2026-09-29)

The host private filesystem channel now exports strict-monotonic task-start,
score, reset-request, and reset-witness timestamps plus full private reset
snapshots and A3→B1 geometry bindings. `raw_lifecycle_adapter.py` joins those
records to each arm's task-level raw events without synthesizing or repairing
timestamps. Three six-task fake-mod handshakes compose with `ArmCoordinator`
route selection and fresh locator checks into the v2 independent raw auditor.
Retained output and H/T/D/C/U are in
[`RAW_LIFECYCLE_ADAPTER_CONSTRUCTION.md`](RAW_LIFECYCLE_ADAPTER_CONSTRUCTION.md)
and `construction/raw_lifecycle_adapter_20260929_03/`: raw SHA-256
`7ba248560ad0b837a7c47cc07fa76c2de9c6b4873da30360c40a6864713a9a24`,
`PASS_CONSTRUCTION_ONLY`, hypothetical `RETAIN`/task-2 break-even, 18 reset
projections, 3 geometry transitions. The persistent fake arm dispatches two
model callbacks while both controls dispatch six. The complete host suite is
86/86. No Java mod, Mindustry, real model, socket, or real task input was used.
No Docker was used because the #5130/#5085 container assignment/release gate
remains in force.

## Fresh-locator → target-dispatch composition (host construction, 2026-10-04)

The branch includes current main through
`446b2635c1ad3b7ed6c97b790c0a35b6fb58d7c3`:
`target_execution_v1.py` composes the existing `ArmCoordinator` fresh-locator
check and receipt-bound `target_dispatch.py` compiler for the two ordered
Mindustry task points. Each point requires a newer observation, current layout
binding, a target-specific image receipt, and a socket clock read before a
single compiled request is submitted. The caller must adapt the live socket's
terminal result into a request-ID-matched receipt that confirms all inputs are
released. Ambiguous or failed receipts stop the task without retry.

Eleven host construction tests verify the two-point order, fresh sequence binding,
stale-geometry refusal before the affected dispatch, task-ID matching, and
fail-closed handling of stale socket clocks, mismatched/nonterminal/unreleased
execution receipts, and repeated calls before lifecycle advance. One test
exercises the real receipt builders and request compiler with synthetic
observations. A mutation control showed that a submit callback could otherwise
rewrite the retained compiled-request object after returning; dispatch now
deep-copies that record before invoking the callback. The target-dispatch tests
pass 11/11, the full package suite passes 97/97, and the inherited decision
probe passes with 10 controls. A synthetic persistent-arm lifecycle walk now
covers A1-A3 followed by the A3→B1 geometry change: the old reference is
classified stale with zero admissions, one repair acquisition occurs, and the
two B1 target requests bind to newer observations under layout B. Its scores,
resets, compiler and socket are simulated callbacks. A second control walks all
three arms across all 18 tasks and 36 ordered point dispatches, checking the
frozen cold/reuse/repair route and model-call schedules. These controls do not
connect a live Mindustry socket, capture real images, dispatch input, call a
model, score a game task, or demonstrate live three-arm execution/economics.
The synthetic raw-v2 and target-dispatch auditors are implemented, but there
is no live raw capture or source-identity proof. Under WSL, socket tests pass
through both a local synthetic server and the actual
`mindustry_three_arm_socket_v2` wrapper plus `stopped_socket_v2` server with a
pipe-backed fake runtime. The bridge test submits 12 actions through one
adapter and verifies the cursor advances from 0 through 12.
Windows skips these AF_UNIX tests because its Python runtime lacks AF_UNIX.
The wrapper's child-entrypoint rewrite is asserted, but the interactive runtime
child and full runner remain unverified. No game, model, Docker command,
workflow, or formal allocation was invoked; the #5130 resource gate remains
controlling.

## Three-arm dispatch + lifecycle raw reconstruction (host construction, 2026-10-04)

After refreshing the branch through current `origin/main` `d22c094a4a2e2292333479573c2eb446c345e1b9`, the private-channel fixture now drives each task through `ArmCoordinator`, two synthetic target-dispatch callbacks, and then the fake-mod lifecycle capture. `assemble_raw_from_private_channels` joins those captured dispatches to the event-level task schedule, including both point admissions/releases and the persistent A3→B1 stale-reference refusal/repair, before the independent raw-v2 auditor evaluates the assembled bytes.

A new immutable construction capture is in `construction/raw_target_dispatch_lifecycle_20261004_03/`. It retains `raw-events.json`, `target-dispatch-events.json`, raw-v2 `audit.json`, independent `dispatch-audit.json`, and `SHA256SUMS`. Raw SHA-256 is `814b5dd83cfe7d963914020db02588a8604548c6e82b4db66493cb88ae1ef8bf`; target-dispatch sidecar SHA-256 is `b3c1eaf0b5093374ee8463cade2217a3197aff938ea968a98e3df7554a48ca66`. The dispatch sidecar is checked by `audit_target_dispatch_capture.py`, which joins each compiled target/request/expected observation sequence with its raw admission, feedback, release, and B1 stale-refusal/repair record. It verifies all 18 tasks and 36 ordered dispatches. Its mutation suite rejects reversed target order, stale request sequence, missing release, an admitted old B1 reference, and malformed observation input. The raw-v2 auditor returns `PASS_CONSTRUCTION_ONLY`, no errors, `RETAIN` as the synthetic evaluator disposition, break-even task 2, 18 reset reconstructions, and 3 geometry transitions. The capture explicitly reports `source_identity_verified=false`: its artifact/model/container/game identity fields are synthetic sentinels, and the result is not live-source verification or an economics experiment. Callback effects remain simulated.

On merge base `d22c094a4a2e2292333479573c2eb446c345e1b9`, the dedicated dispatch/raw mutation suite passes 6/6, the complete package passes 103/103, the inherited efficiency probe passes with 10 controls, and `git diff --check` passes. The exact six sparse-checkout support files were materialized from checked-out Git blobs only for these local checks. No Docker, Actions workflow, Mindustry process, socket, model call, task input, or formal allocation was used; the #5130 shared-resource gate remains in force. See `RAW_TARGET_DISPATCH_CONSTRUCTION.md` for the H/T/D/C/U and scope.

## Durable socket submit trace (host construction, 2026-10-04)

The v2 socket submit adapter now requires an explicit trace sink. Its
`JsonlTraceSink` creates a new file exclusively and fsyncs every JSONL record.
The adapter journals the full compiled request before transport, then journals
the response before validation; a failure writing the pre-send record prevents
the exchange, and ambiguous transport results remain one-shot with no retry.
Calls through one submitter instance are serialized across the complete socket
exchange so concurrent actions cannot reuse an old event cursor or overlap
input operations. An integration test runs the actual submit adapter through
the frozen 18-task synthetic three-arm route using an injected fake bridge:
each arm makes 12 sequential submissions, advances its cursor from 0 through
12, and writes 24 ordered fsynced JSONL records. The dispatch join audits 18
tasks/36 target dispatches and raw-v2 returns `PASS_CONSTRUCTION_ONLY`; source
identity remains false. The full package passes 120 tests after refreshing
through current `main` `0db425b379f9438bf6b13c95dce1b763750b06d5`: 118 pass
and two AF_UNIX cases skip on Windows. Thirteen sparse-checkout support blobs
were materialized from that Git tree only for the tests and removed afterward.
Both AF_UNIX tests pass under WSL; one runs a local synthetic server, while
the other exercises the actual v2 wrapper/server with a pipe-backed fake
runtime across 12 ordered submissions. Python compilation and
`git diff --check` also pass. A fresh
read-only recomputation after this main refresh of
the retained raw-v2 and dispatch-sidecar audits exactly matches the committed
audit JSON: `PASS_CONSTRUCTION_ONLY` with source identity false, and
`PASS_SYNTHETIC_DISPATCH_JOIN` for 18 tasks/36 target dispatches. PR #7370 is
open and Draft. No live socket process, Mindustry input, model call, Docker
operation, or formal allocation was used; the #5130 gate remains active.

The response reader enforces a 1,048,576-byte limit on the received socket
buffer and refuses an oversized line even when its newline arrives in the same
read. This closes a chunk-boundary gap where a single 65,536-byte receive
could exceed the previous loop condition before parsing. A focused regression
test exercises the oversized newline-terminated response.
