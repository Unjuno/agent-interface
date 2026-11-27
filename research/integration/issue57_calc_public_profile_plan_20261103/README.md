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

The archive-to-current-main comparison of the retained live Calc G10 path is
in [CALC_G10_CURRENT_MAIN_CROSSWALK_20261104.md](CALC_G10_CURRENT_MAIN_CROSSWALK_20261104.md).
It confirms that the public Calc adapter composition already exists offline;
the unresolved boundary is live provider/accounting and the frozen comparison,
not another copy of the G10 driver.

The requirement-to-test audit for current main is maintained in
[COMPOSITION_MATRIX_20261103.md](COMPOSITION_MATRIX_20261103.md). The table
below is a compact orientation; its older stale-wait wording is superseded by
the provider-wait composition test described below.

| Requirement | Existing evidence to reuse | Integrated enforcement and regression still required |
| --- | --- | --- |
| #52: abstain on no match, ambiguity, unavailable evidence; preserve partial effects | `runtime/core_v1/test_compiled_gui.py`; `runtime/cli_v1/test_mcp_owned_process.py`; composed wrong/unknown/ambiguous OCR and provider-wait paths below | Fake App Server/Fake X cases reject wrong, unknown, ambiguous, and stale-after-wait inputs before unsafe continuation; remaining live and held-out coverage is listed in the matrix. |
| #53: all-attempt usage and call accounting | `runtime/cli_v1/test_golden_v3.py`, `test_golden_delivery_join.py`; Fake App Server composition and provider-wait repair tests | Synthetic joined path now records timeout, cancelled, malformed, four completed generations, and the separate stale-to-fresh repair. Actual provider reconciliation, retries/skipped stages, and lifecycle totals remain open. |
| #54: schema preflight before GUI authority | Existing `runtime/cli_v1` preflight tests and receipts; composed parser and registered MCP schema/type tests in `test_mcp_endpoint_composition.py` | Top-level arrays, missing required keys, wrong types and pattern violations are refused before the registered handler. The preflight uses FastMCP's own Pydantic argument model; provider raw/usage remain joined. Nested batch constraints and handler-thrown validation errors are covered in the [composition matrix](COMPOSITION_MATRIX_20261103.md) and [Pydantic preflight report](../registered_mcp_pydantic_preflight_20261103/README.md). This does not prove endpoint structured-output compatibility or full generic JSON Schema behavior. |
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

## Provider-ledger pending cancellation composition (2026-11-04)

The separate generic compiled-path regression
`test_partial_input_cancel_accounting.py::test_generic_compiled_partial_input_cancel_polls_same_call_in_ledger`
now binds one synthetic provider attempt to a public compiled MCP request while
Fake X holds a key down. A test-controlled cleanup supervisor forces the public
cancel response to `pending`; the caller then retrieves the same call ID and
cancellation operation through `interface_results` until terminal. The Fake X
cleanup record shows a key release, while the runtime receipt remains
`cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and
replay denied. No second provider attempt, compiled call, input, or recovery is
sent. The full raw provider ledger and Fake X evidence are retained in
`../standard_mcp_task_ledger_57_v1/partial-input-cancel-pending-accounting-20261104-01/`.

This is synthetic cancellation custody/accounting evidence, not successful
runtime release, task effect, bounded recovery, live provider behavior, or live
Calc/WSLc/MAP01 evidence. It narrows the composed pending-response gap; the
positive release-and-fresh-attempt recovery gate remains open.

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

## Same-frame verifier deadline boundary (2026-11-03)

A deterministic regression found a finite-budget edge: the graph could pass its
budget check, then reach the exact deadline immediately before invoking the
opt-in same-frame effect verifier. The runtime now samples the clock at that
callback boundary and yields `SAFE_YIELD/budget_exhausted` without starting the
callback at or after expiry. The effect stays pending, and earlier transitions
remain in the receipt. A focused calibration test exercises the unchanged-frame
Save path. The core/X11 suites pass 81/81 in Windows and pinned Docker, normal
and `-O`; see [the evidence packet](../issue57_effect_verifier_deadline_20261103/README.md).

This prevents post-deadline callback starts; it cannot interrupt a synchronous
callback that began before the deadline. It proves no live Calc result, task
artifact, provider accounting, WSLc, MAP01 or efficiency improvement. #57 stays
open.

## Fresh current-main same-frame live attempt r87-c11 (2026-11-03)

The one-shot Calc/Xvfb run completed and the saved task effect, call/generation-bound Save request, verified enter/save releases, empty close state, natural Calc/oosplash exit, and Docker exit all passed. The preregistered equal-digest condition failed: the final accepted observation digests were distinct, so this is **FAIL_OR_UNKNOWN**, not a live same-frame pass. Raw data and gates are in [r87-c11 report](../issue57_calc_sameframe_live_20261103_r87/README.md). The earlier r84-r86 setup failures remain separately preserved. Next, identify the digest-changing observation signal from raw screenshots/metadata; do not weaken the gate or rerun a consumed attempt. No provider, efficiency, WSLc, MAP01, or broad-reliability claim follows.

r87 raw-image diagnosis found the full-frame digest mismatch is sparse (591/1,024,000 pixels), including the toolbar Save icon after save and small lower chrome/scrollbar pixels; the retained task surface and selected cell appear unchanged. The preregistered full-frame digest condition still failed and remains a failed gate. The next experiment should preregister stable task-surface evidence while retaining raw full-frame images and independent artifact verification.
## Current-main composed suite on pinned Docker (2026-11-04)

The Calc plan, task-artifact verifier, public guarded MCP/owned-process path,
provider-ledger/spool composition, and measurement validator were applied to
current `origin/main` `cf3ddf2f8ef44f78fac3cfed78df2904aa596691` without patch
conflicts. On the cached Xvfb image with network disabled, read-only source and
bounded CPU/memory/PID limits, the 214-test composed set passed in normal mode
(112.157 s) and optimized mode (113.302 s), with Docker exit 0. Exact source
pins, command, stdout/stderr, engine/image identity, and four checksum-covered
packets are in
[`current-main-integration-docker-20261104/`](current-main-integration-docker-20261104/README.md)
and its follow-up directories. The initial run and two fixture-construction
failures remain preserved; the fixture now follows the real observe→mint
provenance contract before checking that launch binding is refused when not
configured.

This is offline synthetic Fake X/provider composition only. No provider/model
generation, live Calc GUI, WSLc, MAP01, token economy, or end-to-end efficiency
was measured. It does not evaluate Docker host stability. Issue #57 remains
open; the matched cold/warm/invalidation/repair lifecycle comparison and live
second-domain boundary remain unresolved.

## Fresh Docker/Xvfb Calc integration result r91-a01 (2026-11-04)

The follow-up [r91 preregistration and raw result](../issue57_calc_sameframe_live_20261104_r91/r91-a01/result-summary.md)
used the registered `calc-ocr-save-v1` path against a fresh Calc process on the
cached, digest-pinned Docker/Xvfb image. Its first reviewed frame passed the
frozen 1280x800 nonblank gate (2,125 unique RGB colors; dominant fraction
0.66922), so the bounded readiness loop added no wait and dispatched no input
before the gate. The sole task then verified A1=731/A2=864 from the saved FODS,
both input releases, neutral close, exact-generation natural exit, identical
frozen task crop, and Docker exit 0. The full 255-file packet is covered by
`RESULT_SHA256SUMS.txt`.

The original frozen audit could not decode the host-written UTF-8 BOM on the
Docker exit JSON. Its original `FAIL_OR_UNKNOWN` record remains intact; a
separate offline recheck differing only in BOM-tolerant JSON decoding passed
all preregistered gates. The `SAFE_YIELD/effect_unavailable` graph outcome is
the designed Save-effect handoff: the registered parent controller binds the
released Save request to the exact call, attempt, process/window generation,
and method-receipt digest, then the post-close verifier checks the persisted
artifact. This is one successful composed-path sample, not a reliability or
efficiency estimate.

R91 used no provider/model generation and has no matched conventional arm.
Thus it adds live effect/release evidence to the Calc composition crosswalk,
but it does not satisfy Issue #57's actual token, resumption, full-lifecycle
latency, cold/warm/invalidation/repair, or second-domain comparison. The shared
WSLc client ownership STOP/HOLD recorded in Issue #7924 also remains separate;
this Docker/Xvfb sample does not clear it.

## Actual App Server provider-usage gate (2026-11-04, R92/R93)

R92-A01 exercised the real Codex App Server worker once but correctly stopped
before `turn/start`: its bare command left `codex_apps` (2,262 tools, starting)
and `cua_repl` (3 tools, connected) active. No model turn, UI input, MCP call,
or Calc effect occurred. This exposed that the worker command helper disabled
feature families but omitted configured MCP-name overrides. The helper now
reads configured MCP names only, disables only existing entries, and retains
the App Server runtime status fail-closed gate. Nine targeted local tests pass.

A retained command-free live check using the repaired worker command reported
only `node_repl` and `openaiDeveloperDocs`, both disabled with empty tool sets;
no model turn was started. A fresh R93-A01 then passed the one-turn provider
usage gate: one schema-constrained read-only image plan, one start/completion,
and exact agreement between terminal usage and the protocol usage event. The
reported usage was 11,938 input, 76 output, 0 reasoning, 0 cached input, and 0
cache-write tokens; all six plan gates passed. The 5.297-second worker duration
is a single observation and has no matched baseline. R93 did not call MCP, send
Calc input, release physical input, or establish task effect. Full R92/R93
summaries and checksums are in
[the R92 follow-up](../issue57_model_usage_preflight_20261104_r92/RESULTS.md)
and [the R93 result](../issue57_model_usage_preflight_20261104_r93/RESULTS.md).

This validates a scoped App Server usage-custody path and fixes an isolation
setup defect. It does not close the matched cold/warm/invalidation/repair
lifecycle comparison, prove upstream provider billing/retry reconciliation,
show lower latency/token use than baseline, or advance WSLc/MAP01 boundaries.
Issue #57 remains open.
