# Issue #57: public Calc profile composition boundary

Status: implementation contract plus a growing offline composition matrix. This
is not a live result, an efficiency result, or permission to consume another
allocation. It uses the already-retained G10 OCR graph and Calc public input-
guard cases as design input; it does not edit or replay their raw evidence.

## Chosen composition

The next coherent path is a server-registered `calc-ocr-save-v1` profile on the
existing owned-process `interface_guarded_compiled` route. The profile is a
fixed, versioned controller adapter for the qualified narrow Calc layout. The
MCP request carries a registered profile ID, an attempt ID and bounded task
data. It never carries Python callbacks, module/import names, executable paths,
arbitrary output paths, or a client-supplied persistence verdict.

Responsibilities remain separate:

| Layer | Owner and contract |
| --- | --- |
| Representation | Existing MCP caller owns the model attempt and its full raw/token ledger. The registered profile ID is a compact selector, not evidence that model work was saved. |
| Execution | Owned child process binds one exact target generation and runs the existing bounded compiled graph. Before each consequential input, a fixed server callback uses the current captured source through `NativeHandleBridge.input_guard`; it cannot capture, mint, retry, or renew. Unknown, stale, modal, deadline-expired, or mismatched OCR refuses the remaining suffix. |
| Feedback | Current source and OCR transcript are retained as bounded receipts; a normal response stays concise and critical failures remain retrievable by exact call ID. OCR is an input dependency check, not task success. |
| Effect | After neutral close/owner retirement, a separate `interface_verify_task(call_id)` reads only the task instance's server-owned saved FODS and scores parsed cells. It emits a separate call-bound artifact-hash receipt; graph `task_success` remains null. Missing, open, or ambiguous output is unknown. |
| Accounting | The outer caller records every provider attempt, including preflight, failure, early stop, repair and verification. It joins to MCP receipts by `attempt_id`/`call_id`; absent provider usage stays unavailable. Cached input remains a subset of input. |

Keep the existing data-only exact-pixel profile unchanged. Exclude generic OCR,
client-selected code or paths, automatic remint/activation, persistent sensors,
new model calls inside the owner, and Docker/WSLc execution from this adapter.
This profile does not claim a general Calc controller or a successful transfer.

## Existing evidence and remaining composition matrix

| Requirement | Existing evidence to reuse | Integrated enforcement and regression still required |
| --- | --- | --- |
| #52: abstain on no match, ambiguity, unavailable evidence; preserve partial effects | `runtime/core_v1/test_compiled_gui.py`; `runtime/cli_v1/test_mcp_owned_process.py`; composed registered-profile wrong/unknown/ambiguous OCR path below | The direct MCP route rejects an already-stale review before worker admission after a simulated wait. Compose a real provider wait with that mutation; preserve child-side checks for the post-preflight race. |
| #53: all-attempt usage and call accounting | `runtime/cli_v1/test_golden_v3.py`, `test_golden_delivery_join.py`; `research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py::test_fake_app_server_generation_is_recorded_through_calc_profile_and_score` | Extend the synthetic timeout-preflight plus success case to stopped, repaired and malformed generations; reconcile against actual provider logs before a live claim. |
| #54: schema preflight before GUI authority | Existing `runtime/cli_v1` preflight tests and receipts | Profile and graph schema rejection occurs before owner admission/input; preflight attempts remain in the outer ledger. |
| #55: dependency revalidation after model wait | `runtime/guarded_x11_v1/test_compiled.py`; `test_input_dependency.py`; Calc public input-guard mutation tests | Change OCR cells, title/modal, sequence, focus, target binding or deadline between observation and input; prove refusal before Save via the real owned-process MCP route. |
| Scope, lease, cancellation, release, bounded progress, uncertain delivery/no replay | `runtime/guarded_x11_v1/test_compiled.py`; `test_input_dependency.py`; `runtime/cli_v1/test_mcp_owned_process.py`; retained R04-R06 and S27-S28 packets | Cancel at partial input and blocked OCR; keep the old call unknown, verify release separately, prohibit suffix replay, then repair only from a new observation/attempt. |
| Independent task effect and collateral | G10's separately parsed saved XML; `runtime/results/calc-public-input-guard-live-01/FINAL_REPORT.md` | Public post-close verifier scores the exact task-owned artifact. Correct file, wrong value, extra cell, missing file and unreadable file each produce distinct typed result; graph success never substitutes. |
| #12/#46 comparison integrity | Existing #57 frozen and audited Calc three-arm, varied-value, temporary-obstruction and lifecycle packets | Freeze task/model/settings, cold/warm/invalidation/repair arms, allowed attempts, order, endpoints, and stop rule. Keep past small-sample blocks separate. |

The registered-profile composition path now exists in
`research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py::test_fake_app_server_generation_is_recorded_through_calc_profile_and_score`.
It sends a synthetic App Server generation through the recorded public Relay to
the registered Calc profile, verifies neutral close/release, scores parsed FODS
cells independently, and keeps the runtime graph verdict separate. The test
also records a timed-out schema-preflight attempt with partial raw bytes and
unavailable usage before the successful attempt; no MCP call is emitted for the
timeout. It then sends wrong-result and unknown-result OCR runs through the same
registered profile and public Relay. Both retain one released input transition,
stop before Save, return `SAFE_YIELD`, and deny replay. The four-attempt joined
summary remains complete while token totals stay unknown because the timeout
usage is unavailable. The injected planner echoes supplied arguments and
reports synthetic usage, so this proves a local composition contract only.

The composed wrong/unknown OCR cases now also include duplicate high-confidence
cell output after one input transition. The parser marks that ambiguous OCR
unknown; the registered profile yields after the partial effect, records the
input release, leaves Save undispatched, and denies replay. This is still a
Fake X regression, not an application-level ambiguity result.

The stale-review MCP check now rejects a sequence superseded during a controlled
20 ms wait and changed window-title cue before scheduling the owner operation.
This is a simulated wait, with no provider request; it does not establish the
provider-to-MCP timing/join boundary. The raw owner and tool receipts are in
[the r02 stale-review packet](../standard_mcp_task_ledger_57_v1/stale-review-after-model-wait-20261103-r02/README.md).

Remaining offline work is to compose an actual provider wait with this mutation
and complete one bounded new-attempt repair case with all receipts joined.
Existing direct-owner, Fake X and recorder tests cover parts separately; they do
not establish those combined paths. No real provider reconciliation or live
efficiency comparison exists.

## Gate before any new live comparison

Complete the remaining composed-path offline matrix first. Freeze code/model,
task values, cold and warm repetitions, invalidation and repair conditions,
all-attempt accounting, timing boundaries and RETAIN/HOLD/REJECT thresholds
before requesting any new allocation. Existing live allocations remain
consumed; this document authorizes no replay. The existing matched Calc blocks
remain narrow evidence: two samples per arm, scripted tasks, cache/provider and
route differences. They cannot be pooled into a population speedup, price, or
reliability claim. Keep MAP01 and WSLc boundaries distinct.


## Post-close exact Calc exit observation (2026-11-03, r75-c1)

A fresh single live attempt passed the preregistered close/release/exit gates. The independent verifier parsed the call-owned FODS as A1=731/A2=864. Both compiled transitions released input; owner close verified empty keys/buttons and exited 0. The parent then observed the exact Calc and `oosplash` generation exit 0 92.712 ms after the release receipt; forced process cleanup was not needed. The independent verifier returned `verified`, `task_success=true`; container exit was 0. All 264 packet files and the packet manifest were locally hash-checked against the frozen source hashes. See [the raw r75 packet](post-close-exit-wait-live-validation-20261103-r75/README.md).

This is one fixed-task live integration result, not provider efficiency, broad reliability, WSLc, MAP01, or Issue #57 completion. r73/r74 failed attempts remain preserved in their original worktree and were not rerun. The source implementation was uncommitted in its source worktree at audit time; this integration branch is the review copy.
