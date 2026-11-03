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

The requirement-to-test audit for current main is maintained in
[COMPOSITION_MATRIX_20261103.md](COMPOSITION_MATRIX_20261103.md). The table
below is a compact orientation; its older stale-wait wording is superseded by
the provider-wait composition test described below.

| Requirement | Existing evidence to reuse | Integrated enforcement and regression still required |
| --- | --- | --- |
| #52: abstain on no match, ambiguity, unavailable evidence; preserve partial effects | `runtime/core_v1/test_compiled_gui.py`; `runtime/cli_v1/test_mcp_owned_process.py`; composed wrong/unknown/ambiguous OCR and provider-wait paths below | Fake App Server/Fake X cases reject wrong, unknown, ambiguous, and stale-after-wait inputs before unsafe continuation; remaining live and held-out coverage is listed in the matrix. |
| #53: all-attempt usage and call accounting | `runtime/cli_v1/test_golden_v3.py`, `test_golden_delivery_join.py`; Fake App Server composition and provider-wait repair tests | Synthetic joined path now records timeout, cancelled, malformed, four completed generations, and the separate stale-to-fresh repair. Actual provider reconciliation, retries/skipped stages, and lifecycle totals remain open. |
| #54: schema preflight before GUI authority | Existing `runtime/cli_v1` preflight tests and receipts; composed parser and registered MCP schema test in `test_mcp_endpoint_composition.py` | A top-level array is rejected before Relay dispatch. An object `{}` is now checked against the registered tool's advertised `inputSchema.required`; the server returns a typed missing-arguments refusal before FastMCP/handler invocation, while the joined ledger retains exact provider raw/usage. |
| #55: dependency revalidation after model wait | `runtime/guarded_x11_v1/test_compiled.py`; `test_input_dependency.py`; `test_calc_provider_wait_stale_refusal_then_one_fresh_attempt_releases` | FakePlanner is held while a title/source cue changes; the old response is refused before input, then a separate fresh attempt proceeds. This is synthetic, not a real provider run. |
| Scope, lease, cancellation, release, bounded progress, uncertain delivery/no replay | `runtime/guarded_x11_v1/test_compiled.py`; `test_input_dependency.py`; `runtime/cli_v1/test_mcp_owned_process.py`; retained R04-R06 and S27-S28 packets | Cancel at partial input and blocked OCR; keep the old call unknown, verify release separately, prohibit suffix replay, then repair only from a new observation/attempt. |
| Independent task effect and collateral | G10's separately parsed saved XML; `runtime/results/calc-public-input-guard-live-01/FINAL_REPORT.md` | Public post-close verifier scores the exact task-owned artifact. Correct file, wrong value, extra cell, missing file and unreadable file each produce distinct typed result; graph success never substitutes. |
| #12/#46 comparison integrity | Existing #57 frozen and audited Calc three-arm, varied-value, temporary-obstruction and lifecycle packets | Freeze task/model/settings, cold/warm/invalidation/repair arms, allowed attempts, order, endpoints, and stop rule. Keep past small-sample blocks separate. |

The registered-profile composition path now exists in
`research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py::test_fake_app_server_generation_is_recorded_through_calc_profile_and_score`.
It sends a synthetic App Server generation through the recorded public Relay to
the registered Calc profile, verifies neutral close/release, scores parsed FODS
cells independently, and keeps the runtime graph verdict separate. The test
also records a preflight-labeled timeout attempt with partial raw bytes and
unavailable usage before the successful attempt; no MCP call is emitted for the
timeout. This is accounting injection, not a schema-compatibility preflight
test. A separate parser-boundary case sends a synthetic completed response
whose agent message is a top-level array. The attempt's reported token usage and
exact raw bytes remain in the provider ledger, while parsing rejects the
non-object before Relay/MCP dispatch. This does not prove conversion or
validation of an object-shaped payload against the registered profile schema.
A second composed test sends `{}` through the real registered Calc MCP tool.
`PublicArgumentMCP` reads the tool's advertised `inputSchema.required` and now
returns `invalid_request` with explicit no-operation/no-input fields before
FastMCP/handler invocation; the provider ledger keeps exact raw bytes and
reported usage. This validates missing required fields only, not property types,
nested constraints or registered-profile compatibility conversion. A malformed
terminal provider result and a cancelled generation are
also retained as attempts with unavailable usage and raw response; neither is
sent to the MCP parser or tool. The test then sends wrong-result, unknown-result, and
ambiguous-OCR runs through the same registered profile and public Relay. Each
retains a released input transition, stops before Save, returns `SAFE_YIELD`,
and denies replay. The seven-attempt joined summary remains complete while token
totals stay unknown because the timeout, malformed, and cancelled-attempt usage is
unavailable. The injected planner echoes supplied arguments and reports
synthetic usage, so this proves a local composition contract only.

The composed wrong/unknown OCR cases now also include duplicate high-confidence
cell output after one input transition. The parser marks that ambiguous OCR
unknown; the registered profile yields after the partial effect, records the
input release, leaves Save undispatched, and denies replay. This is still a
Fake X regression, not an application-level ambiguity result.

The provider-wait MCP composition now holds a FakePlanner generation while the
Calc source/title cue changes, rejects the old response before input, then
completes one separately grounded fresh attempt. Fake X writes the fixture FODS
only on Ctrl+S; the independent parent verifier parses it after close. The
runtime graph result remains `SAFE_YIELD/effect_unavailable`, distinct from the
parent task score. The test passes in normal and optimized Python.

This closes the specific synthetic wait-to-stale-refusal-to-fresh-repair seam.
It does not establish real-provider timing/accounting, a live Calc recovery, a
matched efficiency result, actual provider reconciliation, retry, or full
lifecycle accounting. See the current matrix for exact status and rerun conditions.

## Current-main OCR comparison and same-frame Save follow-up (2026-11-03)

The retained r78–r83 block passed all functional gates in five of six arms;
r80-a6 remains a failed arm due to pre-close artifact verification and natural
exit failures. Its later FODS contents and visible post-task cells do not repair
the missing pre-close proof. The separate [forensic follow-up](../issue57_r80_same_frame_effect_followup_20261103/README.md)
traces the missing Save-request receipt to the graph's same-digest
`no_progress` shortcut, which returned before the effect callback. An offline
change now permits a registered profile to opt into a dedicated unchanged-frame
verifier; Calc uses this only to retain the Save-request receipt and still
returns `effect_unavailable`. This source change has not yet passed a fresh live
Calc attempt. See the
[r78–r83 results](../issue57_ocr_frontier_replication_20261103_r78_r83/README.md),
[r80 forensic follow-up](../issue57_ocr_frontier_replication_20261103_r78_r83/r80-a6/FORENSIC_FOLLOWUP.md),
and updated [composition matrix](COMPOSITION_MATRIX_20261103.md).

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
