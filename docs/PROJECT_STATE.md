# Project state and work order

## Issue #57 successful effect with UNKNOWN usage R05 - 2026-11-23

On current main 8a9cb6d9b99b724732f3baf3caee83d2f043c0bb, a valid synthetic
JSONL response without usage retained the completed caller attempt and
successful synthetic effect. All five totals stayed UNKNOWN; custody audited
execution/effect receipts, and the comparison projector held the assignment
with usage_incomplete_or_invalid. Focused 1/1 and the full nine-test module
pass normal and -O on Windows CPython 3.13.14. This cleanly separates a task
effect from comparison eligibility, but no live provider or GUI was used.
See [R05 packet](../research/integration/issue57_v3_durable_appserver_composition_r05_20261123/RESULT.md).

## Issue #57 failed-turn UNKNOWN-usage R04 - 2026-11-23

On current main d58deb08567325d103eadb7966654907293d10e1, the synthetic
JSONL provider's terminal failed status with no usage notification is retained
as one failed attempt with exact call/thread identity and all five usage
totals UNKNOWN (None). Durable custody audits, neither execution nor effect
receipt appears, the task remains HOLD, and dispatch remains false. Focused
1/1 and the full eight-test module pass normal and -O on Windows CPython
3.13.14. This is synthetic fail-closed evidence, not proof of live provider
completeness or matched efficiency. See [R04 packet](../research/integration/issue57_v3_durable_appserver_composition_r04_20261123/RESULT.md).

## Issue #57 provider success-to-custody R03 - 2026-11-23

On current main 2cf4230f918f1b05990a4491779805cc18658e12, one synthetic
valid JSONL App Server success traversed the production parser/model adapter,
v3 caller, durable Calc allocation writer, and registered ProspectiveRun
custodian. Its exact turn/thread IDs and all five usage counters survived;
synthetic execution/effect receipts audited and one task projected. Focused
1/1 and full module 7/7 passed in normal and -O on Windows CPython 3.13.14.
The prospective run correctly remains HOLD with 17/18 assignments missing and
dispatch disabled. This closes only the offline success-transport seam. Live
provider usage completeness, independent allocation custody, matched
three-arm efficiency, recovered-task repeatability, and preview graduation
remain open. See [R03 packet](../research/integration/issue57_v3_durable_appserver_composition_r03_20261123/RESULT.md).


## Research Preview and #57 current-main follow-up R06 — 2026-11-23

PR #10490 merged the launcher fixture correction at main 7e9caab2; the exact-main WSL post-merge checks passed preflight 19/19, launcher tests 21/21 in both modes, and preview builder/supported-host helper tests 11/11 in both modes. The merged R06 packet also records an isolated WSL-launched Windows Chrome blank-page/window-identity observation; it does not claim GUI input or product task effect. PR #10491 merged the reused-pinned-venv diagnosis at main 8554b2bf: doctor passed 13/15, with only the missing Windows Codex CLI JS entrypoint and dependent codex_cli check failing; current-main audit-retained passed RETAIN. No runtime/package install, browser launch in the doctor trial, model, fresh Golden run, or audit-live occurred. #58 remains open. See [R06 launcher gate](../research/integration/research_preview_current_main_launcher_r06_20261123/RESULT.md) and [R06 host diagnostic](../research/integration/research_preview_reused_pinned_venv_doctor_r06_20261123/RESULT.md).

#57 effect-receipt handoff suite reran 60/60 normal and 60/60 optimized on main 7e9caab2. This is synthetic identity/timing/comparison validation only; live provider usage, recovered task success, repeated reliability, and matched integrated efficiency remain open. See [current-main recheck](../research/integration/standard_mcp_task_ledger_57_v1/effect_receipt_handoff_current_main_recheck_20261123/RESULT.md).

## Current-main WSL Research Preview package follow-up

**Research Preview WSL package R02 (2026-11-23; current main `c5fc0ee0`):** A complete persistent Ubuntu WSL checkout builds the bundle successfully: 29/29 frozen-source hashes match; builder tests 6/6; 22,647 members; checkout/archive static preflight pass; bundle SHA-256 `5850fc0581a47570b542d74198450227da75e010022365f52bc496c17a1b7006`; extracted `audit-retained` passes `RETAIN`. No dependency install, doctor, fresh Golden run or `audit-live`; #58 remains open. This supersedes the earlier sparse/Windows environment diagnosis without erasing it. See [R02](../research/integration/research_preview_current_main_wsl_build_r02_20261123/RESULT.md).

**Research Preview WSL supported-host diagnostic R03/R04 (2026-11-23; source `c5fc0ee0`):** Default system-Python doctor passed 8/15. R04 identified existing Windows Chrome and passed the doctor's configured path-presence check with a temporary WSL override, reaching 9/15; browser launch/control remains unverified. Four Python modules and Windows Codex CLI JS remain missing. No install or live action occurred. Supported-host acceptance, fresh no-retry Golden run and `audit-live` remain open. See [R03](../research/integration/research_preview_current_main_supported_host_r03_20261123/RESULT.md) and [R04](../research/integration/research_preview_current_main_supported_host_r04_20261123/RESULT.md).

## Current-main Linux MCP contract follow-up

R02 resolved the R01 optimized combined-suite timing failure through test-only event notification. The two-second acceptance bounds are unchanged; Docker `test_mcp_server` + `test_mcp_guarded` passed 87/87 normal and under `-O`, with explicit container exit code 0. R01 failure is retained. This qualifies only a local contract suite, not live task effect, recovery reliability, provider accounting, efficiency or release acceptance. See [R02 result](../research/integration/standard_mcp_task_ledger_57_v1/current_main_docker_mcp_linux_r02_20261123/RESULT.md).

**Research Preview Windows builder R01 (current main `39cbd0d2`):** Builder unit tests pass 6/6, but no archive was produced. A sparse Windows checkout initially materialized 26/29 frozen source mirrors with CRLF; exact main blobs reconciled all 29 hashes. The subsequent build correctly stopped because this sparse checkout omits 22 selected tracked files. No dependencies or live acceptance were run. Prior WSL R06 remains scoped to its recorded host/source. See [R01 diagnosis](../research/integration/research_preview_windows_builder_current_main_r01_20261123/RESULT.md).

Updated 2026-11-23 against current `main` `b39d287a1ed5426f3a1ad88218dc4635eca5d9de`; the package and doctor runs remain frozen to source `c5fc0ee00b5fa5208088ee69004a336770336ac4`.
This page is the short project-wide status index. It points to the detailed
receipts; it does not replace their raw evidence or promote a partial result.

## Latest #57 composition results — 2026-11-23

PR #10470 is merged in main `1bf4d236`; it binds the observer only for supervised-win32, with ordinary caller lookup unchanged. R22's final-source combined MCP check passed 94/94 in both modes. R23 reran the Fake public recovery lifecycle as ten independent processes: 10/10 passed (5 normal, 5 `-O`), without estimating live reliability. R167 refreshed full open membership at 1,640 Issues / 406 PRs; PR #10473 has since merged as `31fcd3a2`, and the r168 count-only check reports 1,640 Issues / 405 PRs. R170 exact pagination at main `1d2bdc20` confirms 1,640 Issues / 405 PRs: Issue IDs match r167 and #10473 is the sole PR removal. See [r170](maintenance/repository-inventory-recheck-20261123-r170.md); semantic issue/PR triage remains incomplete. R24 produced one native delayed fixture effect after a 2 s lease, with the public action UNKNOWN/replay-denied; one fresh-session orphan recovery verified release, neutral readback and a 2 s / 78-sample horizon, clearing the exact durable fence. Offline reconstruction scored factual effect true and eligible success false; the original action remains UNKNOWN. The separate-receipt research join passes seven checks in normal and `-O`. On current main `066d70435f`, the Fake App Server → public MCP → Calc profile/FODS-score selector also passes 1/1 normally and under `-O` on Windows CPython 3.11.9; its initial import-path setup failure is preserved in R03. This remains synthetic and does not establish live task success or recovery reliability. R06 source hashes match this main and were reused without replay. R25 froze three attempts but stopped after one recovered UNKNOWN action and one pre-dispatch foreground mismatch; trial 3 was not attempted and no reliability claim is made. R26 then froze a separate one-attempt repeat with explicit Computer Use target activation; exact HWND/PID foreground matched, a delayed post-expiry effect again occurred, and one bounded orphan recovery cleared the exact fence while the action remained UNKNOWN/replay-denied. These native fixtures narrow expiry/recovery behavior only; they are not provider efficiency, MAP01 or reliability evidence. R27 froze and completed three independently activated attempts: each passed exact HWND/PID foreground verification, produced a factual delayed effect after authority expiry, and used one separate recovery that verified release, neutral readback, horizon and exact fence clearing while the source action remained UNKNOWN/replay-denied. This is scoped fixture evidence, not a general reliability rate or eligible task success. Next priority: use existing Chromium/Calc evidence to pin the missing matched lifecycle/accounting seam without duplicate trials; then run the matched #57 all-attempt efficiency comparison when provider/resource conditions are valid. Keep #57 open. See [R24](../research/integration/win32_expired_authority_delayed_effect_r24_20261123/RESULT.md), [R25](../research/integration/win32_expired_authority_delayed_effect_r25_20261123/RESULT.md), [R26](../research/integration/win32_expired_authority_delayed_effect_r26_20261123/RESULT.md), [R27](../research/integration/win32_expired_authority_delayed_effect_r27_20261123/RESULT.md), [R23](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_lifecycle_r23_20261123/RESULT.md), and the [r167 inventory receipt](maintenance/repository-inventory-recheck-20261123-r167.md).



## Current-main public recovered-task repeats R41–R42 — 2026-11-23

R41 passed one frozen public standard-caller trial on main 87b5b459a56c636934947a2fc7616f26150e8b9a. R42 independently passed on merged main dc1f119bcb4094d0b58e70ffa273596f206c6c7a. Both preserved source A as UNKNOWN/no-replay; one orphan recovery verified release, neutral readback and a 2 s late-input horizon; and a distinct fresh HWND/PID generation completed and released one B task with exactly one in-interval event and public task_success=true. Both fixture pairs closed and the durable fence cleared. R42's inherited R34 client-area label is documented as a visual identity caveat; native title/foreground/HWND/PID matched R42.

These are two one-attempt controlled fixture passes on one host, not a reliability estimate, same-window reuse, arbitrary-app, MAP01/Calc, efficiency or Research Preview evidence. R29–R40 setup/target/oracle stops remain retained. See [R41 result](../research/integration/win32_post_recovery_public_task_r41_20261123/RESULT.md) and [R42 result](../research/integration/win32_post_recovery_public_task_r42_20261123/RESULT.md).


## R24 native expiry and orphan recovery

R24 observed one factual delayed fixture effect after authority expiry, while
the public source action stayed UNKNOWN, release-unconfirmed, task-success
null, and replay-denied. The original durable fence stayed unresolved until a
single public orphan recovery verified the matching key-up, neutral readback,
and a full 2 s late-input horizon (78 samples; 32 ms maximum observed gap),
then cleared that exact source fence. Offline reconstruction and a dedicated
research join now derive factual success true but eligible success false and
keep recovery separate from the source action. Seven join checks pass in normal
and `-O`. See the [R24 result packet](../research/integration/win32_expired_authority_delayed_effect_r24_20261123/RESULT.md).

R25's frozen three-attempt repeat stopped after one recovered dispatch and one
pre-dispatch target-foreground failure; the third attempt was not run. R26
explicitly raised the unique target with Computer Use before the foreground
probe and repeated the delayed effect plus one-shot orphan recovery once. The
source action again stayed UNKNOWN and replay-denied while the separate
recovery verified key-up, neutral readback, horizon and exact fence clearing.
Neither cohort estimates reliability. See the [R25 stop/result](../research/integration/win32_expired_authority_delayed_effect_r25_20261123/RESULT.md)
and [R26 repeat](../research/integration/win32_expired_authority_delayed_effect_r26_20261123/RESULT.md).

The first PR workflow exposed an overbroad scope: five ordinary `test_mcp_server` cases patched the observer after server creation and failed because the initial candidate bound the observer for one-shot sessions too. The source was narrowed to use per-server binding only for supervised-win32, restoring the ordinary branch. R21's 94-test combined run then hit WinError 267 only because its temporary path was too deep. R22 reran both complete MCP modules with a short C: path; all 94 tests passed in normal (121.368 s) and `-O` (122.586 s). This is the final candidate's local MCP-module qualification. See [R21](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_observer_scope_correction_r21_20261123/RESULT.md) and [R22](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_scope_corrected_combined_r22_20261123/RESULT.md).

**Observer-binding candidate R14/R15/R16:** R14's narrow delayed-executor test and R15's public compiled-caller callback receipts each pass 1/1 in normal and `-O` focused runs. R16 then ran the full 63-test supervised MCP module once per mode and failed both: normal 12 errors in 527.637 s; `-O` 12 failures plus 16 errors in 867.312 s. The monolithic result has timing spillover and temporary request/report-file cleanup contention; preserve it as a failed broad check, not a candidate pass or reliability estimate. See [R16](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_observer_binding_suite_r16_20261123/RESULT.md). Next isolate the narrow affected tests in fresh processes and diagnose suite interference before another cohort.

R17 ran three representative tests in separate processes with unique temporary roots: all six normal/`-O` runs passed. These selected cases do not reproduce in isolation, supporting (without proving) a suite-context interference explanation. Keep R16 failed; see [R17](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_observer_binding_isolated_r17_20261123/RESULT.md). Return next to the public standard-caller recovery/effect gate after the remaining broad-suite interference is understood.

R18 then ran three R16-failing recovery/caller tests together in one process per mode with separate temporary roots. Both groups passed 3/3 (4.038 s normal, 4.035 s `-O`). The selected cases pass both separately and grouped; this points to full-suite host/run context or cumulative workload without proving a specific cause. Keep the full-module failure and return to the standard-caller recovery/effect gate. See [R18](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_observer_binding_grouped_r18_20261123/RESULT.md).

R19 compared that same three-test group with TEMP under `D:\CodexData\Temp`: normal took 59.060 s and failed with two temp-report cleanup errors plus a caller observer timeout; `-O` took 168.923 s and hit WinError 145. R20 ran the complete 63-test module with dedicated C: TEMP and passed 63/63 in both modes (116.525 s normal; 118.401 s `-O`). This strongly implicates the D: temp path/storage behavior as a test confound, while not identifying its exact OS-level cause. The observer-binding candidate now passes the whole local module on the recorded C: environment; this still does not prove live recovery reliability/effect or efficiency. See [R19](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_temp_volume_r19_20261123/RESULT.md) and [R20](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_observer_binding_suite_ssd_r20_20261123/RESULT.md).

## Recovery lifecycle diagnostics R05–R12 — 2026-11-23

R05's six ordinary caller runs passed but none exercised the timeout drain. R06 and R07 are preserved failed test designs; R08 passed one normal and one `-O` deterministic direct-server delayed-observer Future-drain check, without exercising task/recovery. R09 is mixed at 7/10 and R10 at 8/10; R10's orphan report recorded a real Win32 invalid-HWND observation, `input_dispatched=false`, and owner `call_count=0`. Consequently R04/R09/R10 are not admissible as verified Fake-only lifecycle cohorts. The direct supervised observation injection seam then failed R11 twice because its test asserted the wrong envelope field after raw fake assertions had passed; corrected R12 passed 1/1 normal and 1/1 `-O`, confirming only the minimal direct fake observe seam. It does not resolve R10's longer compiled-caller path anomaly. No additional lifecycle trials were run. Packet manifests for R05 and R08–R12 verify; preserve R06/R07 as failed designs and R10's orphan report.

R13 then passed one normal and one `-O` deterministic direct-observe Future-drain test. It verifies that the same accepted observation Future completes after release and its report finalizes before teardown; each run took about 44–46 seconds. A source audit found a plausible but unproven cause for R10's orphan: `submit()` queues `invoke` on the loop's default executor, and the supervised observe branch resolves module-global `observe` only when that worker reaches the branch. A late worker could therefore outlive a test patch scope. R10 raw does not prove this sequence; keep the anomaly unresolved. See the [R13 packet](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_callback_future_drain_r13_20261123/RESULT.md).

**Current diagnostic gate:** before another lifecycle cohort, make the observer dependency stable for each accepted invocation and retain per-observation callback identity, raw response, owner call count, and dispatch/report worker state across timeout and teardown. Keep the sample count and failure denominator frozen before execution. Do not claim Fake isolation from outer-envelope fields or from the minimal direct-server R12/R13 results.

PR #10467 merged public MCP observe/dispatch/exact-result
lookup with automatic recovery and an independent task oracle. It allows task
verification after automatic completion recovery only when the action remains
UNKNOWN, recovery separately confirms release, and the matching late-input
horizon is verified. The positive composition and unknown-custody negative
control pass 2/2 normally and under `-O`; all external effects are fixtures.
This does not establish native task effect, reliability, efficiency, MAP01, or
Research Preview acceptance. Keep #57 and the project goal open. See the
[R01 packet](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovered_caller_r01_20261123/RESULT.md).

A follow-up candidate isolates the eligibility predicate and adds exact
operation/generation/horizon mismatch controls. Its four focused tests pass in
normal and `-O`; all inputs remain Fake/local. See the
[R02 packet](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_negative_controls_r02_20261123/RESULT.md).

The R04 fresh-process lifecycle experiment ran its frozen ten samples once:
7/10 passed (normal 4/5, `-O` 3/5). Two failures ended with uncertain action
status and release unverified; one failed to accept an observation before its
fixture callback budget. Treat this as a failed repeatability gate and a
timing-sensitive safety signal, not a reliability estimate or pass. Raw logs,
exit codes, conditions, and SHA-256 manifest are in the
[R04 packet](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovery_lifecycle_r04_20261123/RESULT.md).
Post-merge raw-log review also found a `PermissionError` deleting an in-flight
`.report.json.tmp` during the optimized observation-timeout teardown. The
writer's identity and causal role are unknown; a traced cleanup follow-up is
needed.
R03's logging failure is preserved separately and is not scored. Keep #57 open.

## What the project is trying to finish

The project has two connected tracks:

1. **A distributable public runtime:** supported-host setup, bounded and
   inspectable public control, reliable task effects and recovery, and a
   repeatable acceptance path suitable for Research Preview.
2. **Evidence that the runtime is useful and safe:** matched lifecycle cost
   comparisons, independently scored task outcomes, recovery/reliability
   measurements, and preserved experiment custody.

Passing unit tests, fake backends, fixture effects, and a packaged CLI are
necessary pieces. They do not by themselves establish live control, task
success, comparative efficiency, reliability, or preview readiness.

## Gate status

| Gate | Current evidence | Status and remaining proof |
| --- | --- | --- |
| Research Preview / Issue #58 | Frozen RC1 R01 passed launcher preflight 19/19. Current-main R02 passed static preflight and stopped at dependency-install opt-in. Default WSL R03 doctor passed 8/15; R04's one-process Windows Chrome path override passed 9/15, without launching Chrome. Current-main WSL package R02 builds successfully and extracted retained audit passes. | **Open.** Package construction and retained audit are proven; four Python modules, Windows Codex CLI JS, and actual browser-to-WSL control remain unverified, along with supported-host setup, fresh no-retry Golden run and `audit-live`. No install or GUI action occurred. See [package R02](../research/integration/research_preview_current_main_wsl_build_r02_20261123/RESULT.md), [host R03](../research/integration/research_preview_current_main_supported_host_r03_20261123/RESULT.md), and [Chrome configuration R04](../research/integration/research_preview_current_main_supported_host_r04_20261123/RESULT.md). |
| Public standard caller / task outcome | R27 repeated expiry/recovery mechanics 3/3. R41 and R42 provide two independent current-main public recovery-continuation passes: source A remained UNKNOWN/replay-denied; recovery release/neutral/2 s horizon verified; a separate new HWND/PID generation completed B with public task_success true; each fixture pair closed and the fence cleared. R42's inherited R34 client-area label is retained as a visual caveat. | **Scoped pass; gate remains open for breadth.** Two controlled fixture attempts are not a reliability estimate, same-window continuation, arbitrary-app behavior, MAP01, or Calc. Preserve R29-R40 stops and failures; next freeze a finite independent cohort before drawing any repeatability conclusion. |
| Issue #57 integrated efficiency | Historical frozen-source three-arm `integrated-efficiency-live-01` retained 6/6 exact tasks in every arm; persistent was 44.131 s vs plain 56.412 s (-21.8%) and ephemeral 73.238 s (-39.7%), with 26,563 vs 63,128/63,779 input tokens (-57.9%/-58.4%) and observed break-even at task 2. All 29 preregistered sources match the frozen commit blobs. New R01 composes the synthetic App Server failure/usage path through the v3 caller into the durable Calc allocation (2/2 normal and `-O`). R02 records four incomplete outcome envelopes through `ProspectiveRun`; all remain HOLD and dispatch stays disabled (2/2 normal and `-O`). R03 passes one synthetic App Server failed-attempt/usage join into a registered ProspectiveRun custodian (3/3 normal and `-O`), while the task projection remains HOLD. R04 passes caller-level synthetic deferred/known-usage and failed/unknown-usage cases to custody (4/4 normal and `-O`). R05 projects one synthetic successful task with audited execution/effect receipts (5/5 normal and `-O`). R06 completes the offline 18-task three-arm ProspectiveRun with all custodians audited and evaluator `RETAIN` (6/6 normal and `-O`); its comparative metrics are fabricated fixtures. | **Scoped historical/synthetic passes; current goal remains open.** The three-arm evidence is from frozen source commit `54910c6f`, not current main, and one allocation only. R01 uses a local protocol peer, not a provider; the checked-in `.source` mirror has three mismatches. `ProspectiveRun` remains dispatch-disabled and unconnected to a live provider; R02 did not use authentic v3 outcomes or registered task custody; R03/R04 cover synthetic failure, deferred and unknown-usage custody only; live provider comparison, real task/effect evidence, recovery/reliability and cleanup remain open; R06 is not measured efficiency. Still missing is a current-source matched block joining every standard-caller/provider attempt and usage to correctness, latency, release/recovery, and cleanup. See [frozen three-arm report](../research/live_control/results/integrated-efficiency-live-01/report.json), [R01 composition packet](../research/integration/issue57_v3_durable_appserver_composition_r01_20261123/RESULT.md), [source manifest](../research/live_control/results/integrated-efficiency-live-01-frozen-source-v1/SOURCE_MANIFEST.json), and [Issue #57 gates](maintenance/issue57-next-gates-20261121.md). |
| Recovery and repeated reliability | R16 resolves one native orphan-custody case; R23 has 10/10 Fake caller cycles; R27 has 3/3 same-host expiry/recovery cycles; R41 and R42 each have one public recovered-task success on a separate generation. | **Open.** These scopes do not establish a product reliability rate. Preserve all failures/censored attempts in the next independent live standard-caller cases; do not pool fixture, MAP01 and Calc outcomes. |
| Distributable runtime | The WSL Research Preview package build and extracted retained audit passed; the recorded Windows/Ubuntu WSL package suite passed on `d5ada452`. | **Partial.** Construction and basic CLI contracts pass; live native input, permissions, public artifact publication, and the remaining #58 supported-host doctor, fresh no-retry golden run, and `audit-live` gates are unverified. |

## Issue #57 current-main provider timeout custody R06

The frozen synthetic App Server timeout-after-usage case now passes through the actual JSONL parser, grounding model, v3 caller, durable allocation writer, and registered ProspectiveRun custodian. It preserves exact attempt identity and five observed usage counters, creates no task receipts, and remains HOLD with dispatch disabled. Focused and full transport module pass in normal and -O (1/1 and 10/10). Evidence is offline fixture coverage only; provider completeness and matched live economics remain open. See [R06 packet](../research/integration/issue57_v3_durable_appserver_composition_r06_20261123/RESULT.md).

## Repository organization

- The latest GitHub membership receipt is r172: **1,640 open Issues and
  405 open PRs**, bracketed by unchanged main
  `b600070965c48cc9449a87ff31264a5b3604c2d8`. Exact sorted ID sets match r171
  with no additions/removals. See [r172](maintenance/repository-inventory-recheck-20261123-r172.md)
  and [its exact-ID receipt](maintenance/repository-inventory-recheck-20261123-r172.json).
  This remains membership evidence, not semantic issue/PR triage.
  Exact comparison with r152/r157 found no additions; Issues #7748/#7765/#7817
  and PRs #7968/#8181/#10227 are removed. This reconciles the two-PR delta
  previously noted at r163. Counts are inventory, not semantic triage. The full
  family-level routing map is the dated [r160 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md); targeted checks are recorded in [the organization recheck](maintenance/targeted-organization-recheck-20261122.md).
- Do not close or merge items based only on age, unchanged inventory, or green
  checks. PR #10144 remains a Draft research prototype; Issue #7773 remains on
  feasibility HOLD. Other items require their own evidence/custody review.
- The current custody snapshot r173 found **22 registered worktrees: 14 clean
  and 8 dirty**. Dirty trees include untracked experiment packets, local source
  edits, changed raw logs, and a nested `.worktrees/` residue. Preserve all
  until owner/reference and hash reconciliation; nothing was deleted or reset.
  See [r173 custody](maintenance/local-worktree-custody-recheck-20261123-r173.md)
  and its [exact snapshot](maintenance/local-worktree-custody-recheck-20261123-r173.json).
  Follow-up r174 found three root `main` working files already byte-identical
  to current-main blobs, while eight other tracked changes matched no
  registered worktree HEAD. The root checkout is 170 commits behind and still
  requires full custody review; see [r174](maintenance/local-worktree-blob-match-20261123-r174.md).
- Cleanup is therefore **in progress, not complete**: reconcile branch/PR
  reachability, inspect dirty worktrees and raw artifacts by path and hash,
  route every open item to an evidence-backed disposition, then remove only
  verified duplicates whose custody and references are resolved.

## Execution order

1. Continue family-by-family semantic triage and custody reconciliation using
   the r172 full membership baseline; do not infer disposition from counts.
2. Stop repeating the same late fixture-effect experiment. Qualify a standard-
   caller task whose effect can be prospectively eligible, with exact
   recovery/owner evidence and an independent task score; keep failed and
   censored attempts distinct. R24-R27 do not satisfy this task-success gate.
3. Run the matched all-attempt efficiency block only after the measurement path
   can account for every provider attempt and all arms' task outcomes.
4. Close the supported-host Research Preview acceptance gates and verify the
   portable runtime artifact on its declared hosts.
5. Reconcile the broader Issue/PR/worktree queue family by family, retaining
   ideas that lack evidence for closure and resolving custody before deletion.

The overall goal remains active until these gates have direct evidence. Current
source-only and fixture results are useful progress but do not satisfy the live
research or release gates.

## Source records

- [Current goal](CURRENT_GOAL.md)
- [Roadmap](../ROADMAP.md)
- [Repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md)
- [Issue #57 next gates](maintenance/issue57-next-gates-20261121.md)
- [Latest inventory receipt r164](maintenance/repository-inventory-recheck-20261122-r164.md)
- [Worker work map](WORKER_WORK_MAP.md)

## R27 foreground-activated native cohort

R27 explicitly raised each unique fixture through Computer Use and required exact HWND/PID foreground verification before MCP observation or dispatch. All three attempts reproduced the post-expiry factual effect and a separate one-shot orphan recovery. Each source action remained UNKNOWN and replay-denied; all recoveries verified key-up, neutral readback, the full horizon and exact durable-fence clearing. Fixtures closed normally. This is scoped 3/3 controlled evidence, not a general reliability rate. See the [R27 packet](../research/integration/win32_expired_authority_delayed_effect_r27_20261123/RESULT.md).

**App Server stderr transport repair R01 (candidate from main `07c0d7f7`, 2026-11-23):** Current-main client stderr backpressure and bounded close ownership reproduced and repaired. Focused regression tests pass 2/2 in normal and `-O`; the related 14-module App Server suite passes 81/81 per mode with ten platform skips. The broader native protocol attempt is explicitly FAIL/incomplete and its raw Windows/POSIX and dependency errors are preserved. Scope is local transport only. The full project gates remain open. See [R01](../research/integration/standard_mcp_task_ledger_57_v1/appserver_stderr_drain_current_main_r01_20261123/RESULT.md).

**Repository membership r171 (2026-11-23; main `953ce41370666c656278f203dc545aa310947ffe`):** Complete open-Issue/PR pagination matches r170 exactly: 1,640 Issues, 405 PRs, no ID additions/removals, and unchanged main around the read. PR #10478 has merged but was not in either endpoint snapshot. Membership refresh is not semantic triage. See [r171](maintenance/repository-inventory-recheck-20261123-r171.md).

**Draft PR #10144 disposition review (2026-11-23; main `3a705de2`):** Keep it open as Draft. Its 44-commit head is reported 524 commits behind current main, diverges with no merge base, and adds 174 unique paths/13,629 lines. Only the Nov 2 replay-gate check is listed. The author explicitly says the lifecycle prototype is not ready for live use and lists missing restart custody, hard end-to-end bounds, descendant ownership, independent release/scoring, and matched trials. Current-main Calc R01-R06 are synthetic/offline and do not satisfy these gaps. Preserve its unique artifacts while auditing them against current-main records; do not merge or close by age. See [the disposition audit](maintenance/targeted-pr-disposition-10144-20261123.md).

**Current-main Docker/Linux MCP contract R01 (baseline `d18eefdb`, 2026-11-23):** In the cached `issue57-calc-appserver-r88` image with no network and a read-only source mount, current-main public MCP + guarded modules pass 87/87 normally. Combined `-O` fails 1/87 at a 2 s worker-entry wait; the same case passes isolated and both modules pass separately. Preserve this as a combined-run HOLD; no acceptance timeout was increased and no code changed. This proves an environment-specific contract edge remains to diagnose, not live runtime qualification. See [R01](../research/integration/standard_mcp_task_ledger_57_v1/current_main_docker_mcp_linux_r01_20261123/RESULT.md).
