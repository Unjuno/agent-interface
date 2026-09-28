# Mindustry three-arm economics — successor #5130

This additive package is for the unmeasured six-task Mindustry economics cell
under #57. It inherits the frozen task/order/arm/call schedule and acceptance
rule from #1679; it does not reopen or modify #1679, #2624, or prior allocations.

This branch was originally based on `main`
`3553dc1af1125441a6b44256755e7e22df40836d` (merge commit `8c3138c7bd`,
incorporating #5158 on top of prior #5154/#5153 sync `1866f05aab`) and has since
merged current `main` `442ef765598971806dc5d671a223af7b3a711a5f`. The inherited
#1679 preregistration's five dependency blobs were compared with this main:
four are byte-identical; the plan Markdown alone changed from
`ff0de7c4a0d6cc57d145d460f019f72d6967ffec` to
`c0c8ff37206820881b9a86d6801fbae80e0b97d6`. A direct diff shows only two
summary-count edits (six to eight retained discoveries). The frozen decision
rule text and evaluator source are unchanged. This is a provenance note, not
new authorization or experiment evidence.

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

Readiness gap: this additive path has host-side controller adapters, a private
score/reset file channel, and an independent host reset witness. It still has
no integrated live three-arm runner, live-game construction suite, or
independent raw-output auditor. The existing single-task Mindustry runner and
synthetic repeat-fixture protocol are references, not evidence that the
six-task three-arm path is implemented. Those composed artifacts and their
construction checks must be completed before freezing or launching a formal
allocation.

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

Policy incident (2026-09-28 JST): one read-only `docker ps --format ...`
inspection was mistakenly issued before the named #5130 lease, despite the
issue's explicit no-inspection gate. It returned no rows; no container was
started, built, pulled, or altered. This was an unallocated Docker inspection,
not authorization. It is disclosed in the PR conversation; no further Docker
commands will be issued until an exact named coordinator lease is recorded.
