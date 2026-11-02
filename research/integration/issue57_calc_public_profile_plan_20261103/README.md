# Issue #57: public Calc profile composition boundary

Status: implementation contract and test matrix only. This is not a live result,
an efficiency result, or permission to consume another allocation. It uses the
already-retained G10 OCR graph and Calc public input-guard cases as design input;
it does not edit or replay their raw evidence.

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

## Existing evidence and missing composition check

| Requirement | Existing evidence to reuse | Integrated enforcement and regression still required |
| --- | --- | --- |
| #52: abstain on no match, ambiguity, unavailable evidence; preserve partial effects | `runtime/core_v1/test_compiled_gui.py`; `runtime/cli_v1/test_mcp_owned_process.py`; Calc public-adapter wrong/unknown graph cases | Through the registered MCP profile: wrong, unknown, ambiguous OCR refuses Save, retains entered prefix, and never replays it. |
| #53: all-attempt usage and call accounting | `runtime/cli_v1/test_golden_v3.py`, `test_golden_delivery_join.py`; outer recorder in `research/integration/standard_mcp_task_ledger_57_v1` | Join failed, stopped, repaired and successful model attempts to profile call receipts; token fields preserve partial/unavailable semantics. |
| #54: schema preflight before GUI authority | Existing `runtime/cli_v1` preflight tests and receipts | Profile and graph schema rejection occurs before owner admission/input; preflight attempts remain in the outer ledger. |
| #55: dependency revalidation after model wait | `runtime/guarded_x11_v1/test_compiled.py`; `test_input_dependency.py`; Calc public input-guard mutation tests | Change OCR cells, title/modal, sequence, focus, target binding or deadline between observation and input; prove refusal before Save via the real owned-process MCP route. |
| Scope, lease, cancellation, release, bounded progress, uncertain delivery/no replay | `runtime/guarded_x11_v1/test_compiled.py`; `test_input_dependency.py`; `runtime/cli_v1/test_mcp_owned_process.py`; retained R04-R06 and S27-S28 packets | Cancel at partial input and blocked OCR; keep the old call unknown, verify release separately, prohibit suffix replay, then repair only from a new observation/attempt. |
| Independent task effect and collateral | G10's separately parsed saved XML; `runtime/results/calc-public-input-guard-live-01/FINAL_REPORT.md` | Public post-close verifier scores the exact task-owned artifact. Correct file, wrong value, extra cell, missing file and unreadable file each produce distinct typed result; graph success never substitutes. |
| #12/#46 comparison integrity | Existing #57 frozen and audited Calc three-arm, varied-value, temporary-obstruction and lifecycle packets | Freeze task/model/settings, cold/warm/invalidation/repair arms, allowed attempts, order, endpoints, and stop rule. Keep past small-sample blocks separate. |

The single missing composed-path check is: **a public owned-process MCP call
selects the registered profile, executes the bounded graph with its trusted OCR
input guard, terminates neutrally, then a distinct verifier scores the exact
saved artifact by call ID, while the outer all-attempt ledger joins actual
provider usage without changing the graph's `task_success=null`.** Component
unit tests and prior direct-owner live cases do not establish this connection.

## Gate before any new live comparison

Implement and pass the composed-path offline suite first. Freeze code/model,
task values, cold and warm repetitions, invalidation and repair conditions,
all-attempt accounting, timing boundaries and RETAIN/HOLD/REJECT thresholds
before requesting any new allocation. Existing live allocations remain
consumed; this document authorizes no replay. The existing matched Calc blocks
remain narrow evidence: two samples per arm, scripted tasks, cache/provider and
route differences. They cannot be pooled into a population speedup, price, or
reliability claim. Keep MAP01 and WSLc boundaries distinct.
