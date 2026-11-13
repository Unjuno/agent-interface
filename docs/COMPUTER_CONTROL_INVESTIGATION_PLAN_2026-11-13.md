# Computer control investigation plan — 2026-11-13

## Purpose

Move the computer-control goal forward by closing the currently visible gap between a recovered/released input and a verified MAP01 task outcome. Keep each uncertainty classified separately: caller evidence integrity, deadline/expiry, OS input state, application queue/task effect, and terminal task oracle. Do not promote a neutral input horizon to proof that queued application work is absent.

## Verified starting facts

- The active thread goal still exists and is active. A second goal cannot be created while that goal is unfinished; continue it rather than replacing it.
- At the time this plan was first written, its main worktree was clean at `195fc6cdd2b1f30396fd5c846225c7fb04c172b4`; this is a historical snapshot, superseded by the current status below.
- R156 is a composed-path FAIL/UNKNOWN. Its independent sampler observed W down 8.0001 ms after the lease expiry and first fully-post-expiry up at 9.2503 ms; a later state read showed release, but the public receipt lacked release confirmation and the task oracle was not reached.
- R156's runner then failed on missing `expiry-held-w-samples.json` while the server reported a pending-call resolution error. The target was kept open for one state read, but not for the required continuous two-second post-run horizon. The click/task effect therefore remains unknown.
- A separate, exact-source orphan recovery later released W and left mouse on a fresh target generation, verified neutral readback and a two-second horizon (77 observations, max gap 30.018 ms), kept the original action UNKNOWN and replay denied, and cleared durable custody (revision 428). This is recovery evidence, not R156 task-success evidence.
- R157 preregisters the focused correction: keep expiry samples separate from pending resolver records, use exact call-id reconciliation, observe a bounded independent two-second same-generation neutral horizon on normal and exception paths, and require every existing task/effect gate before close.
- At planning time the R157 packet was not yet frozen or run. Its freeze script's tautological runtime-tree comparison and bytes/path hash mismatch were corrected before freezing; the outcome and remaining untested branch are recorded below and in the R157 report.

## Investigation questions

1. Does R157's exception path preserve a valid public result for the exact dispatched call without confusing expiry sampler data with resolver output?
2. Can the independent neutral observer prove continuous same-process, same-generation release within its bounded sample-gap and read-bracket limits?
3. Does the public action receipt confirm release independently of the sampler, and does the same-run ammo oracle plus demo audit distinguish task effect from later queued/application effects?
4. Are any terminal failures caused by the integrated runtime/caller, the evidence join, the observation boundary, target/environment, or the task oracle?
5. Only after correctness gates pass: what remains to produce a comparable #57 efficiency estimate with all failed attempts retained?

## Finite execution plan

1. **Prepare and freeze:** repair the R157 freeze-script tautology; compile runner/helpers; run the focused repository tests for evidence joining and neutral-horizon sampling, plus the packet's adjudication/contract tests. Freeze source, runtime/research hashes, package identity and clear custody state. Verify the freeze before launching a target.
2. **One fresh integrated run:** execute the preregistered single-dispatch R157 public compiled-supervised MAP01 attempt. Preserve every raw file and initial failure. No retry or replay. Keep the target open through the independent horizon and exact-call reconciliation; close only after all predeclared release and task gates pass.
3. **Classify before changing code:** adjudicate runtime release, expiry bracket, held-input evidence, horizon, numeric ammo transition, task-oracle receipt and scoped demo trace separately. If a gate fails, stop that attempt and repair only the demonstrated seam in a new frozen source/attempt.
4. **Record and integrate:** write an additive result report with source and raw hashes, exact conditions, outcome, limitations, and the next decision. Promote only a demonstrated fix with local tests. Keep unrelated Docker settings, runtime-download UX and Calc economics out of this MAP01 experiment.
5. **Then resume #57:** design matched same-model comparisons with all attempts, actual token/model usage, end-to-end latency, correctness and release gates. Existing small or instrumented observations do not establish a speedup.

## Stop and acceptance rules

- At most one dispatch in R157. Never replay an uncertain action.
- Missing/stale identity, generation, exact-call receipt, release evidence, neutral horizon or task oracle means FAIL/UNKNOWN for the corresponding claim.
- Release success does not imply task success; a two-second neutral input horizon does not establish application-queue quiescence.
- A task-effect pass requires independent same-run numeric change 50→49, exact final dispatch/call linkage, valid public task-oracle receipt, and the preregistered demo audit.
- No speed claim from this single instrumented run. Report local checks separately from live evidence and any optional CI.

## Status and next action

R157 completed one native run. Its 18 release/task checks and scoped demo audit passed; the raw packet's 105-file post-run manifest and four-file adjudication addendum verify with no hash mismatches. The frozen source was a docs-only task-branch commit atop main, so the report records that provenance deviation. The run exercised normal pending resolution, not the exception-only result-reconciliation branch.

Next, add a deterministic local integration test that injects pending terminal/result-query failures and proves the exception branch remains exact-call-only, non-replaying, and UNKNOWN when receipts are missing. Then decide whether another live attempt is necessary. Do not repeat a live allocation solely to obtain the same already-passed normal-path result.

### Current status after R160/R161 (2026-11-13)

The current authoritative source checkout is `72d8bcdc8fb4b4e7fd12c95394d21fde45aa3a12` (`research/map01-r158-candidate`); `origin/main` matched this commit when checked. R160 and R161 are separate immutable native attempts in task-local packets. R160 reached one dispatch but its runner raised after dispatch because the packet omitted `capture_timing_audit.py` and its independent screenshot path did not wire full frames through the fixed ROI. Its additive audit remains separate from its original hold.

R161 is one fresh native scoped pass: one public dispatch, QPC expiry bracket 8.1086 ms, sampled W down 5.9882 ms after expiry, same-generation release/readback and two-second late-input plus independent-neutral horizons, public and independent 50→49 effect, and a same-run demo audit with no recorded forward command in its conservative post-expiry interval. The final additive adjudication passes 17/17. It is one observation, not a reliability estimate, hard latency bound, proof of application consumption, MAP01 completion, or #57 efficiency result. The complete limits and measured cancellation/recovery stage offsets are in [the R160/R161 report](../research/integration/map01_recovery_deep_trace_r160_r161_20261113.md); raw, conditions and hashes remain in the task-local `work/map01-native-r161-candidate/` packet.

R161 showed that the phase-only durable `cancel_pending` update overlapped recovery. Current source intentionally schedules supervisor cancellation first because admission has already durably recorded unresolved custody. If the phase-only write fails, the prior unresolved record remains and verified recovery is still required before resolution. Raw stage traces localize the 4.9265 ms cancel-to-recovery interval: producer retirement occupies 4.7397 ms; recovery exchange starts 0.0554 ms after retirement returns. This one run does not show the wait is avoidable or characterize its distribution.

The reusable full-frame transition helper and pinned R161 templates now have local coverage in `research/integration/map01_numeric_ammo_oracle_20261111/`: 8/8 focused tests pass under Windows CPython 3.14.2 in both normal and optimized mode, and applying the helper to the exact retained R161 frames reproduces 50→49 with the R161 template hashes. This is a research-oracle change; no runtime semantics changed in this batch.

Issue #57 remains open. Its current body contains distinct Calc fixed-task, varied-value, and temporary-obstruction comparison blocks; R161 must remain outside those token/latency arms because it used a different native MAP01 task and no matched route comparison or model-usage accounting. The producer-retirement source path and targeted ordering regressions were inspected; both passed 2/2 in normal and optimized Python. They support retiring the exact producer before cleanup but do not characterize native latency. No runtime change is justified. Next, proceed to the exact-base diff review and integration of this narrow full-frame oracle/report work; only preregister another native run if a distinct unresolved boundary is identified. Keep all first outcomes and the 20 ms boundary unchanged.

### Clock-only public stdio follow-up

The real parent-to-stdio-server `interface_clock` path now has a direct regression on Windows 10 / CPython 3.11.9, and a paired no-input diagnostic compared CPython 3.11.9/GetTickCount64 with CPython 3.13.14/QPC. Mixed runtimes were outside the parent clock brackets in 0/8 samples; the same-runtime 3.13/QPC control was inside in 8/8. This supports the existing rule to use one interpreter for QPC timing and to keep server deadlines in the server clock domain; it does not establish action-endpoint acceptance or a native release guarantee. The stdio and mixed-runtime evidence, raw samples and hashes are in [the clock follow-up report](../research/integration/windows_mixed_python_clock_20261113/RESULT.md). The previously referenced DCLK-R01/X01 packet is absent from this source checkout, so its historical raw hashes remain unverified here.

### Windows custody-suite CI and remaining integration boundary (2026-11-13)

PR #10274 merged as `d1b8e1bb651d15dd14d4eb23ea1aeacb35e65d98`; it retains the R160/R161 oracle/report and mixed-clock diagnostic with both raw runs. PR #10275 merged as `bad1914586f5fea24d1df37f9d82f2d029446160` and adds `runtime.cli_v1.test_mcp_supervised_win32` to the Windows CLI CI matrix. Its first run failed at import because the matrix had no MCP SDK. After adding the repository-pinned `mcp==1.30.0` and `Pillow==10.2.0`, all Windows/Ubuntu/macOS CLI jobs and replay-gate passed; the Windows job ran the 25-test supervised custody suite successfully. The suite also passed locally on Windows CPython 3.11.9, 25/25 normal and 25/25 under `-O`.

The existing `test_late_recovery_after_dispatch_return_promotes_action_receipt` exercises a real 800 ms expiry wait with fake producer/supervisor, delayed recovery publication, exact-call result polling, confirmed release, action progress evidence and independent task-oracle adjudication. This materially strengthens deterministic composition coverage, and the CI now keeps it running on Windows. It remains fake-backend evidence: tests call `server.call_tool` directly rather than a spawned stdio process, and do not prove real OS input release or GZDoom task effect. The mixed-runtime experiment also only reads `interface_clock`; it does not submit a deadline.

PR #10277 merged as `b1cd802dfaef5266b09b52e93e9b38493f56c17b` and closes that subprocess boundary. The test-only child server injects a fake producer/supervisor and accepts an action with a 1.5 s server-clock expiry. The parent uses MCP stdio, waits past expiry, polls `interface_results` for that exact call ID, then invokes `interface_verify_task`. It observed terminal `recovered`, `release_confirmed=true`, action lower bound 2, task success null until the oracle call, an independent oracle `failure`, and replay denied throughout. The dedicated case passed on Windows CPython 3.11.9; the whole 26-case suite passed 26/26 normally and under `-O`; the Windows CPython 3.12 CI suite and all PR checks passed. This is subprocess/framing integration with fake custody; it is still not a physical input release or GZDoom effect.

### Exception custody across spawned MCP sessions (2026-11-13)

A follow-up Windows-only composition test now drives a producer exception through a spawned source MCP server, obtains its exact terminal action receipt over stdio, and constructs the source custody record from that receipt. The source action stays `UNKNOWN` with release unconfirmed, `task_success=null`, and replay denied. A separate fresh stdio server is then given that exact source call/operation/generation and the new target generation; its fake supervisor performs a real two-second wait and records the measured release-to-observation interval, after which the public tool returns recovered with the configured horizon verified. The original source is never upgraded to successful or replayable. The path passed on Windows CPython 3.11.9; the full 27-case supervised MCP suite passes 27/27 normally and under `-O`, including the earlier normal expiry/delayed recovery case. This validates public stdio framing, custody handoff, exact identity binding, and fail-closed UNKNOWN semantics with fake Win32 ownership; it does not establish real native input release, target application response, or GZDoom task effect. The test-only recovery adapter's horizon clock fields are measured around an actual two-second wait, not synthesized as a future timestamp.

The next boundary is native application evidence. No `gzdoom.exe` or R160/R161 task-local raw packet was available in the current checkout or searched user install/workspace locations, and no GZDoom process is running. The registered GPU-control connector offers only a disabled, unrelated TinyStories CPU workload; it cannot allocate this target. Do not launch a substitute target or treat Docker Linux as native Win32. Reacquire the existing isolated GZDoom fixture and its IWAD, then preregister one fresh dispatch with the unchanged expiry/release/task gates and raw frame/receipt manifest; stop on UNKNOWN. Keep #57 matched efficiency separate.
