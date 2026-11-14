# Compiled Win32 composition and clock contract (2026-11-14)

## Goal and current disposition

Advance the existing compiled GUI path through caller selection, final target
revalidation, guarded native execution, receipt retention, and independent task
effect verification. Preserve the distinction between a returned execution
receipt and verified application success. This note records one integration
repair and the evidence needed before Issue #57 can decide RETAIN/HOLD/REJECT.

**Disposition: HOLD for efficiency claims.** The bounded MAP01 expiry block
found repeatable scoped effects in two 120 ms held-click trials, but it is not a
matched model/token/cost comparison. The Fake X composition verifies code-path
mechanics only. No live general-purpose GUI or provider economics claim follows.

## Integration path and repaired defect

The current composition is:

1. `adaptive_acquisition_caller_v3` selects and finally revalidates a target.
2. `integrated_efficiency_compiled_execution_v2` builds the compiled interface
   from that final selected target and retains the returned core receipt.
3. `runtime.core_v1.compiled_gui` performs bounded local transitions.
4. `runtime.guarded_x11_v1.compiled._Adapter` connects fresh observations,
   native target admission, execution/release receipts, and effect predicates.
5. The caller's outer verifier decides task effect independently of graph
   completion.

The public Win32 caller now bounds read-only `interface_observe` retries when
the server returns transient `busy` immediately after a pending action's exact
`interface_results` readback. It makes at most three additional calls, waits
10 ms between them by default, records each refusal in
`standard_target_evidence`, and never retries input. Persistent busy yields
`SAFE_YIELD / association_changed` without dispatching a suffix.

The existing native composition tests failed on this Windows host because the
adapter mixed clock domains. The caller-facing core uses
`time.perf_counter_ns`; the guarded adapter had supplied observations and graph
deadlines using `time.monotonic_ns`. On this host those counters have different
origins, so a valid post-action observation could appear older than the action,
or an observation could appear to be in the future. The graph then yielded
`stale_observation` before verifying effects.

The guarded adapter now uses `perf_counter_ns` for graph observations, budget
deadlines, and post-release settle accounting. Native lease/fencing deadlines
remain on `monotonic_ns`; they are a separate contract and are not compared to
graph timestamps. The raw native `capture_ns` remains retained for freshness
and forensic timing; the graph timestamp records when the synchronous capture
result returned to the graph in the graph clock domain.

## R180 retained-result caller correction

The exact retained R180 public result omitted the redundant
`action.obligations` field while preserving the accepted `standard_program` and
the separate cancellation recovery receipt. Main commit
`1af9fef9e47f6a97433d50b8246ea3fcd12bc131` re-derives obligations from that
same stored program, checks the source generation, and joins the exact
cancellation obligations before accepting release custody. The same retained
row now classifies as `delivery_uncertain` with verified release and
`input_dispatched=true`; task success remains unknown and replay remains
forbidden. Wrong-button and stale-generation controls remain fail-closed.

The retained R180 strict-runner attempt itself remains
`PARTIAL_EVIDENCE_STRICT_RUNNER_GATE_STOP`; this is a caller projection repair,
not a new live run or a retrospective change to the frozen attempt. In
particular, the separate stdio exception test in this branch has no complete
late-input horizon and therefore remains `uncertain`, even when the recovery
receipt contains a release boolean. The caller may invoke an independent task
oracle only for a release-verified `delivery_uncertain` result; that oracle
verdict does not complete the compiled graph or rewrite the original action.

## Requirement-to-evidence crosswalk

| Requirement | Existing implementation/evidence | Remaining boundary |
|---|---|---|
| #52 target ambiguity/unavailable refusal | v3 caller final target revalidation; `test_compiled_caller_handoff_v2.py`; guarded native composition changed-generation cases | Live perception and provider route remain unqualified |
| #53 attempt/token accounting | v3 caller attempt ledger and phase timing; `integrated_efficiency_compiled_execution_v2.py` returns detached core receipt | This Fake X path has no model attempts; no model usage or cost can be inferred |
| #54 result schemas | core typed outcomes and public Win32 receipts; adapter receipt copies | Full external receipt durability still belongs to the sink/storage layer |
| #55 dependency/admission | guarded X11 bridge revalidates generation, scope, target dependencies and release; `test_compiled_native_caller_composition.py` | Real target recognizer accuracy and actual application effects remain open |
| Runtime safety | bounded transitions/deadline, refusal on stale/unknown state, release receipts, no automatic replay | Blocking real callbacks and physical release timing need host-level evidence |
| Independent effect | inner effect predicate and caller outer verifier stay separate; wrong/unknown value and sink-failure tests | Fake X predicates are synthetic, not an independent application scorer |
| Comparison integrity | existing integrated-efficiency harness records task attempts and stage timings | No frozen matched baseline/optimized/integrated Win32 sample set exists |

## Local verification performed

The in-process Fake producer integration drives `run_public_compiled` through
the MCP server tools: public observe, pending dispatch, same-call-ID result
query, transient-busy retry, task-effect verification, and the exact-call task
oracle. It also makes a second controlled producer call that returns an
exception with unverified release; the caller retains uncertainty and skips the
effect verifier and task oracle. The recovered-dispatch caller test additionally
exercises the R180 result projection through `run_public_compiled`: the source
action remains `unknown` with no release, task-success, or replay claim; the
exact accepted program supplies omitted action obligations, and a matching
bounded cancellation receipt confirms release. The public caller yields
`SAFE_YIELD / delivery_uncertain` while recording a separately valid exact-call
task-oracle result. Removing the native release-attempt proof still fails
closed. A separate stdio MCP test runs `run_public_compiled` against
a child server over MCP stdio. It joins the pending result by exact call ID,
accepts nested `call.call_id` while the query is pending, and preserves UNKNOWN
action delivery when the recovery receipt lacks a bounded late-input horizon.
An adjacent unit test exhausts the retry budget and proves no dispatch occurs.

The public caller and MCP server integration modules pass 43 tests in both
normal and optimized Python mode:

```text
runtime.cli_v1.test_supervised_win32_compiled
runtime.cli_v1.test_mcp_supervised_win32
```

The earlier five-module selection below also passes 39 tests in each mode.

On the Windows host and candidate branch, the following five modules pass in
both normal and optimized Python mode (39 tests each):

```text
research.live_control.test_compiled_native_caller_composition
research.live_control.test_compiled_caller_handoff_v2
research.live_control.test_compiled_callback_caller_failures
runtime.cli_v1.test_compiled_dispatch_composition
runtime.cli_v1.test_supervised_win32_compiled
```

Commands:

```powershell
python -m unittest research.live_control.test_compiled_native_caller_composition research.live_control.test_compiled_caller_handoff_v2 research.live_control.test_compiled_callback_caller_failures runtime.cli_v1.test_compiled_dispatch_composition runtime.cli_v1.test_supervised_win32_compiled
python -O -m unittest research.live_control.test_compiled_native_caller_composition research.live_control.test_compiled_caller_handoff_v2 research.live_control.test_compiled_callback_caller_failures runtime.cli_v1.test_compiled_dispatch_composition runtime.cli_v1.test_supervised_win32_compiled
```

These are local Fake X/adapter checks. They do not exercise a live Win32 or
Linux GUI target, a model provider, actual user task correctness, or physical
input release latency.

## MAP01 bounded block and stop boundary

The finite native Windows block recorded R187-R192. R189 failed before input
because the runner's independently observed foreground window was the host
application. The split activation protocol then allowed R190-R192 to reach
GZDoom. R190's zero-dwell click did not change the HUD (ammo 50→50). R191 and
R192 used a 120 ms down/up dwell and each changed ammo 50→49; each recorded
separate recovery release, neutral horizons, and a 16 ms expiry-to-release
receipt. Each process exited normally and custody was clear at the end.

The 120 ms condition therefore passed 2/2 scoped task-effect attempts after a
zero-dwell result of 1/2. This is a small descriptive contrast, not a causal
reliability estimate. The broad scene-motion threshold did not pass in R191 or
R192; the local HUD effect classifier did. The bounded live block is closed at
R192. Do not add another isolated dwell trial as a substitute for the
composition/efficiency work below.

## Required next comparison before any efficiency disposition

Freeze one task distribution, app/version, target, input budget, model/config,
providers, stop rules, and scorer before starting a comparison. Include every
attempt, including acquisition failures, repair, timeouts, and wrong effects.
Compare these three arms on matched tasks and order:

1. **Plain/current baseline:** ordinary observe → model decision → bounded
   standard input → independent effect check.
2. **Optimized non-symbolic:** same model and task with the strongest existing
   batching/cache/local-repair mechanism but no compiled symbolic continuation.
3. **Integrated compiled path:** the v3 caller, final-target interface build,
   bounded graph, native admission/execution, retained receipts, and the same
   independent task scorer.

Record per attempt: success/effect correctness, all task/model generations,
input and image calls, visible images, token usage per stage, model wait,
local observation/admission/execution/release time, acquisition and repair,
end-to-end elapsed time, and direct cost where available. Missing usage or
cost is **unknown**, never zero. Report per-arm attempt counts and uncertainty;
include cold, warm, invalidation, and repair cases. Decide RETAIN/HOLD/REJECT
only from this integrated ledger.

Calc remains a separate second-domain requirement: its current evidence has no
matched arms or complete token/model accounting. MAP01 correctness/recovery and
general efficiency remain separate evidence boundaries. Keep Issue #57 open
until the matched integrated comparison and its raw/conditions are retained.
