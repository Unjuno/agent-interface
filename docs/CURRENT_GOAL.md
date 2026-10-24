**WSLc current-main private-Xvfb S28 same-condition replicate (2026-10-25):** a fresh independent 3,930 ms trial passed the same 29-check gate as S27. Cancel response was 307.093 ms; release readback 3,987.763 ms, independent all-up readback 4,108.399 ms, and delayed-event horizon 8,502.318 ms. Old and fresh-session task oracles passed; the original public runtime result remains UNKNOWN/replay-denied/`task_success=null`. Transaction margin was 4.798 ms, compared with S27's 7.198 ms. The two samples suggest repeatability under this synthetic condition but do not establish a hard guarantee, live GUI, MAP01, efficiency, or reliability. The new session terminated; its unique 228,589,568-byte VHDX is hash-recorded in [S28](../research/integration/wslc-currentmain-xvfb-blocked-release-s28/POST_CLEANUP.json) and remains retained.

**WSLc current-main private-Xvfb boundary S27 (2026-10-25):** one preregistered 3,930 ms trial passed its scoped gate with a 7.198 ms margin to the 4 s transaction deadline. Public cancel returned in 313.663 ms; release readback completed at 3,985.903 ms, independent all-up readback at 4,075.391 ms, and the delayed-event horizon stayed clear at 8,501.695 ms. Old-task and fresh-session recovery oracles both passed, while the original runtime call correctly remained UNKNOWN/replay-denied/`task_success=null`; exact container/image/session cleanup passed. Audit 29/29. See [S27](../research/integration/wslc-currentmain-xvfb-blocked-release-s27/RESULT.md). This is one synthetic private-Xvfb sample between S23's 3,920 ms pass and S25/S26's 3,940 ms failures; it does not establish a timing guarantee, live GUI, MAP01, matched efficiency or reliability. The session was freshly named and exact-name scoped; shared WSLc ownership remains unresolved. The unique WSLc session's 227,540,992-byte storage VHDX remains after termination with its hash in `POST_CLEANUP.json`; no deletion was performed.

**WSLc current-main private-Xvfb boundary series S23-S26 (2026-10-25):** S23 passed at 3920 ms with an independently verified release receipt 13.123 ms before the 4 s deadline, separate all-up readback at 4358.689 ms, and 8502.055 ms late horizon (audit 25/25). S24 is retained as a zero-input setup failure caused by missing asset paths; container/image/session cleanup succeeded. S25 at 3940 ms produced a release receipt 7.614 ms before deadline, but independent all-up readback at 5002.641 ms missed the 5 s bound by 2.641 ms (audit 24/25; fail). A fresh S26 at the same 3940 ms pause crossed the transaction deadline by 3.5165 ms; the public result stayed UNKNOWN/no-replay/task_success=null and emitted no release/task oracle (audit 22/22). These samples bracket a near-deadline change between a narrow pass at 3920 ms and safety-bound failures at 3940 ms; they do not establish a deterministic timing guarantee or general reliability. All evidence is private synthetic Xvfb, not physical GUI, real application, MAP01, or efficiency results. See [S23](../research/integration/wslc-currentmain-xvfb-blocked-release-s23/RESULT.md), [S24](../research/integration/wslc-currentmain-xvfb-blocked-release-s24/OUTCOME.json), [S25](../research/integration/wslc-currentmain-xvfb-blocked-release-s25/RESULT.md), and [S26](../research/integration/wslc-currentmain-xvfb-blocked-release-s26/RESULT.md).
**WSLc current-main private Xvfb blocked-release S21/S22 (2026-10-25):** S21 is preserved as a pretrial setup failure caused by CRLF in the container init script; no Xvfb/caller test input ran, and exact container/image/session cleanup succeeded. The distinct S22 WSLc 3.0.3 attempt passed the public standard-caller Xvfb test at a 3860 ms pause. Release readback completed at 3921.388 ms after admission (78.612 ms before the 4 s deadline); independent parent readback was 4219.074 ms; the delayed-request horizon was 8502.261 ms. Old and fresh synthetic task oracles passed, while public runtime state remains UNKNOWN/replay-denied/task_success=null. Audit: 25/25. This is private synthetic Xvfb evidence only, not physical GUI, real application, MAP01, efficiency or reliability evidence. See [S21](../research/integration/wslc-currentmain-xvfb-blocked-release-s21/OUTCOME.json) and [S22](../research/integration/wslc-currentmain-xvfb-blocked-release-s22/RESULT.md).
**WSLc current-main saturated-relay cancellation S19/S20 (2026-10-25):** S19 is retained as a pre-test runner setup failure: all 31 wheel hashes passed, but its lockfile path did not exist; no unittest/Fake X event ran, and container/image/session cleanup passed (audit 8/8). A distinct S20 corrected that path and passed `test_saturated_relay_stdout_dispatches_cancel_to_held_fake_x_caller` on WSLc 3.0.3. With 16 ordinary responses queued behind blocked stdout, cancel reached the standard caller and Fake X readback emptied its synthetic key/button state 115.290 ms after admission; this readback preceded stdout resume by 114.244 ms. The response was written after stdout resumed. Public state remained UNKNOWN, release-unconfirmed, task_success null and replay denied. The 12-check audit passed. Synthetic Fake X only: no physical release, real GUI/MAP01 effect, task success, efficiency or reliability claim. Unique session VHDX retained with hash. See [S19 setup failure](../research/integration/wslc-relay-cancel-saturation-currentmain-s19/RESULT.md) and [S20 result](../research/integration/wslc-relay-cancel-saturation-currentmain-s20/RESULT.md).

**WSLc current-main Fake X target-generation refusal S16-S18 (2026-10-25):** S16 and S17 stopped before image/container/test because the scoped exact-name list returned exit 0 with empty stdout and the harness wrongly required JSON. Both sessions terminated; those attempt IDs remain setup failures. S18 corrected the parser and passed one standard-caller generation-mismatch test on WSLc 3.0.3.0 / CPython 3.12.14. The source/current generations differed; the public call refused before input (`input_dispatched=false`, no Fake X press receipt), `task_success=null`, replay denied. Thirteen raw records passed a 20-check audit. No real GUI/OS input, release/recovery, MAP01, or task-success result. The three unique session VHDXs remain, individually hashed; no global inventory or other allocation was queried. See the [S16-S18 packet](../research/integration/wslc-currentmain-fakex-generation-refusal-s16/RESULT.md), [S17](../research/integration/wslc-currentmain-fakex-generation-refusal-s17/RESULT.md), and [S18](../research/integration/wslc-currentmain-fakex-generation-refusal-s18/RESULT.md).

**Local current-main Fake X delayed old-DOWN R01 (2026-10-25):** one local standard-caller regression passed; 8 raw receipts were hash-manifested and the post-run audit passed 12/12. A modeled late key-down followed a separate empty-state release readback, and public state correctly remained UNKNOWN/no-replay with `task_success=null`. This validates the conservative synthetic contract only; event ordering is modeled, not observed from real X. It is not WSLc or live-GUI evidence. The later S19/S20 WSLc attempts used fresh exact-name-scoped sessions under explicit user authorization to use this PC; they did not query global inventory or touch another session. This updates that local readiness note for those synthetic Fake X checks only; live GUI/MAP01 remains open. See [R01](../research/integration/currentmain_fake_x_late_down_caller_local_20261025_r01/RESULT.md).

**WSLc current-main Fake X standard-caller S15 (2026-10-25):** one fresh isolated WSLc 3.0.3.0 session on current main `0024d763a106753eb8059cf6828417dca4467a58` passed the standard-caller blocked-Fake-X-reply cancellation test with 24 raw records and an independent 18-check audit. Three identity replies agreed on one target generation. Cancellation returned in 124.228 ms; owner retirement occurred, but the synthetic disconnect stayed UNKNOWN, so release was not attempted, task success stayed null, and replay stayed denied. No real X, desktop, application, MAP01, efficiency or reliability claim. See the [S15 result](../research/integration/wslc-fakex-standard-caller-currentmain-s15-3a94a47ddf42/RESULT.md). S12/S13 setup failures and S14's pass without event receipts are retained separately; the S15 manifest formatting correction is additive.

**R31–R46 runtime correction:** those historically `wslc_`-named runs used Docker Desktop, not WSLc. Their results count only as synthetic-Xvfb Docker evidence. See the [runtime erratum](../research/integration/wslc_standard_caller_xvfb_20261025_R31-R46_RUNTIME-ERRATUM.md); frozen raw outcomes were not changed.
**Docker Desktop/Xvfb standard-caller R31–R46 (2026-10-25; runtime-label correction):** R31–R36 stopped before input. R37–R41 passed at 3,500–3,800 ms; R42 at 3,900 ms exceeded the 4 s transaction deadline by 4.988 ms. Near the edge, R43 passed at 3,850 ms with 27.552 ms margin, R44 failed at 3,875 ms by 0.466 ms, and independent R45/R46 repeats passed at 3,860 ms with 20.877/18.848 ms supervisor margins and parent readbacks at +4104.230/+4108.282 ms. Passing trials reached the late-event horizon and both synthetic task oracles; runtime custody remains UNKNOWN, replay denied, and task success null. See the [R31–R46 rollup](../research/integration/wslc_standard_caller_xvfb_20261025_R31-R46.md) and [R46 result](../research/integration/wslc_standard_caller_xvfb_20261025_r46/RESULT.md). Synthetic Xvfb only; Win32/MAP01, real-app transfer, matched efficiency, and broad reliability remain open.

**WSLc transaction-budget boundary R28–R30 (2026-10-25):** R28 passed a 2,900 ms private-Xvfb pause under the 3 s transaction deadline with 35.908 ms left. R29 increased the pause to 2,950 ms; the server resumed 101.597 ms before deadline, but the worker returned UNKNOWN at timeout and the public test failed before independent task oracles. Commit `aaa4fce67440fcd475e71e3134345f5649336f39` increased only the internal transaction budget to 4 s and added a Fake X regression for a release worker completing after 3.2 s. The regression failed before and passed after the change, in normal and optimized CPython 3.12.3. R30 repeated R29's 2,950 ms pause on the changed source: release/readback beat the 4 s deadline by 995.384 ms; independent key readback and old/fresh task oracles passed; runtime custody stayed UNKNOWN and replay denied. One trial per condition, synthetic Xvfb only; no Win32/MAP01, production task-success, efficiency, or reliability claim. See the [R28–R30 rollup](../research/integration/wslc_standard_caller_xvfb_20261025_R28-R30.md) and raw packets.

**Win32 paired R50/R51 follow-up (2026-10-24):** R50's strict phase-1 release audit passed 11/11, but the paired attempt remained `FAIL_OR_UNKNOWN` (8/13) because its dashed UUID oracle ID was rejected by the public verifier; the exact fixture effect existed, but no accepted bound task receipt was returned. R50 is preserved and was not replayed. A fresh R51 added an input-free 32-lowercase-hex oracle-ID guard, passed preflight 14/14, phase 1 11/11, and the combined audit 13/13. Its callback stayed held 1,400.3203 ms after cancel; 89 exact-call polls and 74 same-generation Q-up samples were recorded, and recovery Q-up returned after 310.6963 ms. The separate fresh-generation task produced a success receipt bound to its new call, operation and target generation. The initial dispatch response correctly leaves `task_success` null; the subsequent standard `interface_verify_task` response is `status=verified, task_success=true` ([raw response](../research/integration/win32_supervised_standard_caller_20261024_r51/run/phase2_task/verify-task-0.json)). Neutral release/readback passed. The effect-file write-return to oracle-read-start interval was 256.4395 ms, not physical input-to-effect latency. The later session-close receipt's `release_confirmed=false` is separate: close does not issue a new release, so action-level release evidence is in the retained action receipt. R44, R47, R48, R49 and R51 are paired fixture passes, not a broad reliability estimate. See the [R50 failure](../research/integration/win32_supervised_standard_caller_20261024_r50/RESULT.md) and [R51 corrected replication](../research/integration/win32_supervised_standard_caller_20261024_r51/RESULT.md). Both used native Windows only; WSLc remains STOP/HOLD under [#7924](https://github.com/Unjuno/agent-interface/issues/7924). Real-app/MAP01 transfer, matched efficiency and broader reliability remain open.

**Win32 paired R52/R53 continuation (2026-10-24):** R52 stopped before input because its owned fixture could not obtain a Computer Use activation receipt (preflight 15/15; zero dispatch/cancel; no phase 2). R53 passed its strict phase-1 release gate 11/11: the Q-up callback stayed held 1,403.6837 ms after cancel, recovery Q-up returned at +637.0034 ms, and independent same-generation readback observed it at +641.936 ms with 73 eligible samples during the hold. Its phase 2 then timed out before activation, with zero dispatch/cancel/task effect; the combined outcome remains `FAIL_OR_UNKNOWN` 3/14. Both stop outcomes and hash verification are captured in the [redacted R52/R53 packet](../research/integration/win32_supervised_standard_caller_20261024_r52_r53_public/README.md); neither is a task-success sample. R54/R55 are later fresh paired passes and remain separately reported below.

**Win32 paired R54/R55 follow-up (2026-10-24):** two more fresh native-Windows attempts on the authorized PC passed the phase-1 strict release gate (11/11) and combined audit (14/14), then completed a separate fresh-generation task through the public verifier (`status=verified`, `task_success=true`) with independent exact-effect and neutral-release/readback evidence. Recovery Q-up was returned at +619.7598 ms and +632.4875 ms after cancel; same-generation readback observed it at +621.229 ms and +638.4985 ms while the injected callback remained held for 1,404.9483 ms and 1,402.8097 ms. Same-host `perf_counter_ns` intervals and R54's retained activation-helper exception are detailed in the [redacted R54/R55 packet](../research/integration/win32_supervised_standard_caller_20261024_r54_r55_public/README.md). Both 71-entry private manifests were verified; raw host/path/process/window metadata remains local and is not claimed as publicly re-auditable. The six runtime files pinned by the attempts are unchanged from source commit `0f6464a` through current main `d954307`. These two fixture passes narrow native-Windows release and task-effect uncertainty; they do not establish WSLc behavior, matched efficiency, MAP01/real-app transfer or broad reliability.

**Win32 supervised standard-caller R42–R49 update (2026-10-24):** local-Windows attempts R42–R47 are indexed in the [R42–R47 rollup](../research/integration/win32_supervised_standard_caller_20261024_r42_r47/README.md), preserving each outcome separately. R42 passed its strict release phase but phase 2 stopped on a harness `NameError`; R43 independently verified a new-generation task effect but was not paired with release; R44 passed one paired release/task sequence; R45 missed the frozen 1,250 ms hold gate by 4.9554 ms and correctly did not start phase 2; R46 passed release but phase 2 stopped on a runner invocation error; R47 passed one paired sequence, with a 1,405.5285 ms callback hold and independent task oracle. R48 and R49 independently passed the same strict release gate (11/11) and fresh-generation task oracle (combined 13/13). R49 held the callback 1,410.2225 ms after cancel response, with 90 same-call polls and 74 eligible same-generation Q-up samples; its exact fixture effect passed and effect-write to oracle-read-start was 220.5783 ms. Both R48 and R49 phase-2 actions had neutral release/readback, while each later session-close receipt said `release_confirmed=false`; runtime `task_success` remains null. R44, R47, R48 and R49 are paired fixture passes, not a reliability estimate. See the [R48 packet](../research/integration/win32_supervised_standard_caller_20261024_r48/RESULT.md) and [R49 packet](../research/integration/win32_supervised_standard_caller_20261024_r49/RESULT.md).

Merged [PR #9502](https://github.com/Unjuno/agent-interface/pull/9502) closes the R47 crosswalk's synthetic compiled-graph → supervised Win32 caller composition gap. The test retains the completed prefix and refuses a generation-stale suffix before producer start. Remaining gates include real-app/MAP01 transfer, matched efficiency and repeated reliability. WSLc remains STOP/HOLD under [#7924](https://github.com/Unjuno/agent-interface/issues/7924); R42–R49 used native Windows only.
**Win32 input-free foreground eligibility R01 (2026-10-24):** after the exact owned fixture was activated through the Computer Use window API, the separate Win32 backend returned from `focus()` and an independent foreground read matched the target. Backend emissions remained zero; the fixture recorded only `ready`, and no effect was produced. Focus subtest is `PASS_SCOPED`; the whole attempt is `FAIL_OR_UNKNOWN` because its process exit code was not retained after WM_CLOSE, despite process/window disappearance. No retry, release, recovery, task-success, or WSLc evidence. See [R01](../research/integration/win32_focus_eligibility_input_free_20261024_r01/RESULT.md).

**Win32 R39/R40 input-free setup failures and R41 foreground boundary (2026-10-24):** R39 stopped in preflight because its inherited R37b file hashes did not match two current-main runtime files; R40 stopped before input because the clean checkout lacked its referenced R36 raw/audit files. R41 used a new ID and current-main hashes; its preflight passed 11/11. The live public dispatch then failed at the first `focus` operation (`foreground focus verification failed`), before any pointer/key emission (`backend_emissions=0`, `input_dispatched=false`). The fixture recorded only `ready`; no Q-hook event or public cancellation occurred, so the strict release audit is 2/10 and the fresh-generation task phase was not started. The action remains UNKNOWN with `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`; close stayed busy because completion readback was non-neutral. Producer, sampler, fixture and hook exited; the fixture window disappeared and foreground restoration passed. This is a focus/dispatch failure, not a release sample or task-success sample. No WSLc allocation was used. A later native fixture regression recorded `SetForegroundWindow=False`, foreground still different from target, and zero emissions; the failure does not identify the OS policy. See the [public PC eligibility and WSLc boundary record](../research/integration/win32_pc_wslc_eligibility_20261024/RESULT.md).

**WSLc compiled-control core R01 (2026-10-24):** On current main `5e378a4`, the cached WSLc image ran 37 compiled-GUI and conservative release-recovery tests successfully under Python 3.14.8. This confirms software-contract compatibility for that isolated test set only. Memory hard-limit enforcement is unverified because the WSL kernel lacks swap/cgroup limit capabilities. The separate composed Fake X standard-caller attempt R01 stopped at import because the image lacks the MCP SDK; no test body or synthetic input ran, and exact-CID cleanup was verified. See the [core result](../research/integration/wslc_compiled_core_20261024_r01/RESULT.md) and [composed caller result](../research/integration/wslc_fake_x_standard_caller_20261024_r01/RESULT.md).

**Win32 supervised caller + task oracle R03 (2026-10-24):** one fresh fixture
passed the exact public observation → generation-bound validation/dispatch →
same-call retained result → server-configured task-oracle path. The dispatch
returned pending at 10 s; five read-only same-call lookups reached completed.
The fixture's exact click/save/token effect passed, terminal all-up and separate
neutral readback passed, the oracle receipt matched call/operation/generation,
server and fixture closed, and foreground restoration was confirmed. R01/R02
startup/response failures remain preserved; R02's fixture did complete, but its
5 s caller timeout prevented the public oracle call and remains
FAIL_OR_UNKNOWN. R03 is one fixture sample only; blocked-I/O release, recovery,
MAP01, reliability, efficiency, and WSLc GUI remain open. See the [R03 packet](../research/integration/win32_live_task_oracle_20261024_r03/RESULT.md).
**Win32 R36 strict public-cancel release gate (2026-10-24):** one fresh
fixture/dispatch with same-generation Q-down baseline and one recorded public
cancel passed the finite gate. Cancel response 1.266 ms; callback remained held
1252.120 ms after cancel response; 78 exact-call status polls covered the
1251.953 ms hold. Recovery Q-up SendInput returned at +627.600 ms; an
independent same-generation sampler recorded 59 Q-up samples before callback
return, exited cleanly with 602 samples, and a final separate readback was
neutral. Matched terminal recovery receipt, exact producer exit, fixture/app
cleanup and foreground restoration passed. `interface_close` nevertheless
reported `release_confirmed=false`, and no second Q-up hook callback appeared.
The click/save effect preceded cancellation; a later `q` char event followed;
runtime `task_success` remains null. Strict bounded release is PASS for this
single Win32 attempt only; reliability, task success, MAP01, WSLc and efficiency
remain open. See [R36](../research/integration/win32_supervised_standard_caller_20261024_r36/RESULT.md).

**Win32 standard-caller recovery → fresh-generation task-oracle construction check (2026-10-24):**
the standard `interface_dispatch` / `interface_cancel` / `interface_results`
path now has a local synthetic regression that recovers an old-generation call,
keeps its task outcome unknown and its retained result unchanged, then dispatches
and independently scores a distinct call under a new target generation. The
new task receipt must match its exact call, operation and generation; one oracle
invocation is allowed. The focused 88-test public MCP/Win32/session/oracle set
passes in CPython 3.11.9 in both normal and `-O` modes, and the research workspace
index passes. This is a construction check with fake processes and oracle; it is
not live evidence, WSLc evidence, MAP01, or a reliability estimate. R37b now
adds one live paired sequence; the regression still covers the controlled old-
UNKNOWN/fresh-generation boundary locally. See
`runtime/cli_v1/test_mcp_supervised_win32.py::test_standard_recovered_cancel_then_fresh_generation_task_success`.

**Win32 R37b bounded recovery → fresh-generation task effect (2026-10-24):**
one new native-Windows sequence passed the unchanged R36 strict release audit
(10/10), then completed a separate task on a new fixture and target generation.
Phase 1 held the Q-up callback 1,250.649 ms after a 2.039 ms cancel response,
with 77 same-call polls; recovery Q-up returned at +626.382 ms, and 57
same-generation samples observed Q-up before callback return. A final readback
was neutral. Phase 2 began after cleanup, used one new observation/validation/
dispatch, retrieved the exact pending call with five read-only polls, and the
server-side oracle verified the exact click/save/token effect against the new
call, operation and generation (`task_success=true`). Combined audit: 11/11
`PASS_SCOPED`, one paired sample only. Both `interface_close` responses said
`closed` but returned `release_confirmed=false`; phase 1 had no second distinct
Q-up hook callback, and phase-1 task effect preceded cancellation. WSLc was not
used; MAP01, efficiency, broad reliability and real-app transfer remain open.
R37a's input-free root-path preflight failure is preserved separately. See the
[R37b packet](../research/integration/win32_supervised_standard_caller_20261024_r37b/RESULT.md).

**Win32 R38d timestamped task-effect observation (2026-10-24):** one fresh
native-Windows fixture run completed one public observation, validation,
dispatch, five read-only result polls and one exact-call server task-oracle
check. The click/save/token effect matched; the task receipt matched call,
operation, target generation and oracle ID; terminal release and neutral
readback passed; fixture cleanup and foreground restoration passed. A
packet-local fixture timestamped the effect-file write. The raw event-to-oracle
difference was 265 ms, but this host's `monotonic_ns` uses `GetTickCount64()`
with 15.625 ms reported resolution; the conservative interval is 249.375–280.625
ms. The effect occurred 797 ms after the caller received `pending`. This is one
fixture timing sample, not matched efficiency or reliability. R38/R38b/R38c
setup failures are preserved; R38d's frozen audit schema error is also preserved
with a corrected additive audit over unchanged raw. No WSLc or Docker was used;
MAP01, real-app transfer and matched efficiency remain open. See the
[R38d packet](../research/integration/win32_task_effect_timing_20261024_r38d/RESULT.md).

**Win32 R35 terminal-release diagnostic correction (2026-10-24):** R35 did
not record a public `interface_cancel`; the exact producer completed normally
with verified terminal `release_all`. After the final Q-up SendInput return and
before its held hook callback returned, the independent same-generation
sampler recorded 48 `Q=false` samples. This qualifies normal terminal-release
state observation only, not cancellation recovery. The callback lasted
1490.357 ms, but only 4 status polls were recorded against the strict 21-poll
gate; observer teardown ended `unknown`, no second Q-up hook event appeared,
and runtime `task_success` remains null. The original R35 classification in
PR #9479 was too strong; source inspection found hold_ms used before its local
assignment, raising UnboundLocalError before interface_cancel; [the correction](../research/integration/win32_supervised_standard_caller_20261024_r35/correction.json)
and [corrected result](../research/integration/win32_supervised_standard_caller_20261024_r35/RESULT.md)
preserve the raw trial and supersede it. Strict R29 remains FAIL_OR_UNKNOWN.

**Win32 proven-down release boundary R33 (2026-10-24):** one fresh public
stdio-MCP attempt passed the 10-check input-free preflight and independently
read `Q=true` for the fixture's exact generation before cancellation. The exact
recovery `VK_Q` key-up `SendInput` returned at +619.931 ms; a second process
read `Q=false` for that same generation at +930.848 ms, while the Q-up hook
callback remained blocked until +1237.935 ms after cancellation. Public polls
first reported recovered/release-confirmed at about +983 ms (four of 20 polls);
the fixture's click/save/empty-text oracle matched at save time. Strict result
stays FAIL_OR_UNKNOWN: the frozen gate requires at least 21 held polls (20 recorded),
and no second Q-up hook event was observed. A posthoc evaluator repairs the
frozen audit script's missing `readback` binding and snapshot-timing bug, but
does not change this result. The raw also records a post-save `q` char event;
runtime task_success remains null. See [R33](../research/integration/win32_supervised_standard_caller_20261024_r33/RESULT.md).

**Win32 exact Q-up isolation R32 (2026-10-24):** the corrected no-text fixture
matched click/save/empty-text exactly. During a 1258.489 ms held Q-down callback,
the exact recovery Q-up `SendInput` returned after 310.487 ms; `release_all`,
recovery receipt, observer neutral receipt, and four public recovered polls all
arrived before callback return. The hook never observed Q-up, the early separate
state sample preceded recovery, and the producer exited after callback return;
strict audit remains FAIL_OR_UNKNOWN (17/20). This separates software release
receipts from proof that Q-up reached the target. See [R32](../research/integration/win32_supervised_standard_caller_20261024_r32/RESULT.md).

**WSLc isolated local runtime smoke S01 (2026-10-24):** WSL/WSLc 3.0.3.0; the
exact pinned Python image inspect returned not found. One unique-name `--pull
never` run stopped with `WSLC_E_IMAGE_NOT_FOUND` before writing a full CID or
executing application code. A read-only query for that generated name returned
no match; no container mutation or unrelated inventory query occurred. This is
HOLD/UNKNOWN, not a WSLc pass or shared-allocation clearance. See [S01](../research/integration/wslc_local_runtime_smoke_20261024_s01/RESULT.md).
**Win32 recovery-boundary trace R31 (2026-10-24):** one fresh fixture retained
its Q-down callback for 1245.455 ms; all 20 same-call polls stayed
pending/release-unconfirmed and strict audit was FAIL_OR_UNKNOWN (18/20).
The recovery helper's `release_all` spanned the callback; four initial Unicode
compensating key-up `SendInput` calls each took about 299–314 ms, and the fourth
crossed callback return. The exact Q-up returned about 8.3 ms after callback
return. This timing is consistent with a blocked native injection boundary but
does not prove kernel causality. The R31 task-effect oracle also had a copied
R30 text operation; actual click/save/text are preserved raw but the declared
R31 sentinel mismatched, so no retry was made. See [R31](../research/integration/win32_supervised_standard_caller_20261024_r31/RESULT.md).
**Win32 retirement-call trace R30 (2026-10-24):** with one fresh native
fixture and a 1,253.867 ms blocked-hook hold, all 20 same-call polls remained
`running / pending / release_confirmed=false`; strict audit 19/20
FAIL_OR_UNKNOWN. A test-only trace on the exact producer showed
`OperationCancellationSupervisor._retire_process` returned true about 8.6 ms
after cancel start: `terminate()` took 0.366 ms, `join(0.1)` 4.128 ms, then
`is_alive()` was false. Process retirement therefore did not span the blocked
hook interval in this sample. The callback returned after the hold and only
then did recovery/all-up/readback finish. The remaining recovery helper /
`SendInput` boundary is the next instrumentation target; its blocking is still
a hypothesis. See [R30](../research/integration/win32_supervised_standard_caller_20261024_r30/RESULT.md).

**Blocked-hook boundary R29 (2026-10-24):** the fresh current-main Windows
trial held the owned low-level Q-down callback for 1,304.466 ms after a 1.336
ms cancel response. All 21 same-call polls during the hold remained
`running / pending / release_confirmed=false`; the frozen audit is
FAIL_OR_UNKNOWN 19/20 on release while blocked. A separate same-generation
Q-up observation during the hold is nondiscriminating because the Q-down had not
passed the hook. After callback return (1,306.210 ms after cancel start), exact
producer exit, recovered/all-up receipt, same-generation neutral readback,
fixture effect, and cleanup passed. This narrows the R14 result to one current
main fixture; kernel scheduling cause and other Windows paths remain unknown.
WSLc remained HOLD per #7924's uncached-image/unknown-cleanup record. See
[R29](../research/integration/win32_supervised_standard_caller_20261024_r29/RESULT.md).

**Standard-caller exact-call retrieval repeat R28 (2026-10-24):** on the
current #9470 main commit (`380e1a9`), a fresh supervised Win32 fixture again
returned `pending` after the supported 10,000 ms dispatch wait. One dispatch was
issued; six read-only `interface_results` polls for the exact call ID reached
`completed` 11,052.806 ms after dispatch start. The producer's verified all-up
receipt was timestamped at 10,826.954 ms; independent neutral readback, the
exact one-click/38-character/one-save fixture oracle, public session close,
fixture exit, and foreground restore all passed. Strict R28 audit: 14/14 PASS.
The public close response itself still reports `release_confirmed=false`; the
terminal action receipt is the verified release evidence. R27 is independently
reproduced once on current main, not a reliability claim. This remains a local
Windows fixture result, not WSLc, blocked-I/O release, MAP01, runtime task
success, or matched efficiency. R28 packet preserves an initial sparse-checkout
preflight stop and a first audit attempt's field-name mismatch; neither sent
additional input. See [R28](../research/integration/win32_supervised_standard_caller_20261024_r28/RESULT.md).

# Current objective and working direction

**Dispatch lock repair (2026-10-24):** the dispatch worker now exits after a
verified `recovered` or terminal `unknown` cancellation, allowing its shared MCP
operation lock to be released before the lease deadline. A public-path
regression reproduces recovered cancellation and requires session close within
a 150 ms bounded retry window. The targeted supervised Win32, owned-session and
composition modules pass 42 tests in normal and `-O` Python. The relay test's
observation does contain `source.sequence` and a process-generation digest; a
minimal public observe/close call confirms that contract. The full CLI run's
actual failure is later: `test_saturated_relay_stdout_dispatches_cancel_to_held_fake_x_caller`
times out waiting for `held-reply.json`. Its Fake X caller emits a KeyPress and
then a KeyRelease before `GetPointerControl`; the offline proxy candidate clears
its pending-press association on that intervening request, so it forwards the
later sync reply instead of holding it. The test then leaves an owner IPC worker
blocked during executor shutdown. This is an unresolved event-order mismatch
between the composed caller and test-only relay candidate, not a missing public
observation field. The complete suite has not produced a summary.

**Standard-caller blocked-hook trial R14 (2026-10-24):** the one-shot public
stdio-MCP run is preserved in the [R14 result](../research/integration/win32_supervised_standard_caller_20261024_r14/RESULT.md).
It held one injected Q-down inside the owned low-level callback for 700.934 ms
after cancel. The cancel returned pending in 1.431 ms; eleven exact-call polls
all retained `running / pending / release_confirmed=false`, and the callback
was still blocked at hold end. An independent same-generation process saw Q-up
during the hold, but this does not prove release because Q-down had not passed
the hook. After callback return at 701.097 ms, exact producer exit and recovery
UP followed; final independent readback was neutral, the fixture saved its
sentinel, session/hook/fixture cleanup passed, foreground was restored, and
runtime `task_success` remained null. The frozen audit is FAIL_OR_UNKNOWN
19/20 on the blocked-I/O release check. Public close also reported
`release_confirmed=false`. The next boundary is a safe way to retire or fence
the blocked producer before recovery UP, without permitting late input, while
preserving UNKNOWN until independent neutral readback. This was a
user-authorized Windows-PC test, not a WSLc allocation. No rerun.

**R15 hook-timeout trial launch (2026-10-24):** R15 prepared a 1250 ms
low-level hook hold to test the documented Windows timeout boundary, but its
source preflight refused to start because this page had an uncommitted tracked
edit. The failure happened before output-directory/fixture/hook creation, MCP
dispatch, or native input (`caller_dispatches=0`). Preserve it as a prelaunch
failure; do not rerun R15. Its conditions and source are in the
[R15 packet](../research/integration/win32_supervised_standard_caller_20261024_r15/RESULT.md).
The next attempt needs a clean committed source SHA and a new attempt ID.

**Standard-caller cancellation R13 (2026-10-24):** the repaired public stdio-MCP
path passed its frozen auditor 19/19 on one fresh owned fixture. Same-call
polling reached injected Q-down in 775.292 ms; one cancel returned in 1.495 ms,
then exact producer exit, `recovered / release_confirmed=true`, and independent
same-generation Q-up were observed within 235.151 ms of cancel. `interface_close`
returned `closed` on its first call in 90.154 ms; fixture exit, hook exit and
foreground restore passed. The fixture saved the exact R13 sentinel while
runtime `task_success` remained null. This verifies the specific R12 lock-release
repair for one Windows fixture; it does not establish MAP01, efficiency, broad
reliability, or WSLc transfer. See the [R13 packet](../research/integration/win32_supervised_standard_caller_20261024_r13/RESULT.md).
**Standard-caller cancellation R12 (2026-10-24):** the first pre-admission
`unknown_call` was recorded, subsequent same-call polling reached the hook in
1.003 s, and one cancel returned in 1.479 ms. Exact producer exit preceded hook
UP; public results reached `recovered / release_confirmed=true`, independent
same-generation readback observed Q-up, and the exact fixture effect was saved.
The audit is FAIL_OR_UNKNOWN 18/19 because close stayed busy through 37
attempts/4 s. Source inspection locates the likely cause: the dispatch worker
continues while action status is `running` after cancellation has reached
`recovered`, retaining the shared MCP operation lock. No local child remained;
public close still did not confirm. The next step is a local regression and
minimal exit-condition repair before another one-shot live check. See the
[R12 result](../research/integration/win32_supervised_standard_caller_20261024_r12/RESULT.md).

**Standard-caller cancellation R11 (2026-10-24):** 250 ms polling of the
returned public call ID advanced execution to injected Q-down in 984.654 ms.
The callback was held through a 1.699 ms public cancel response; the exact
producer exited, hook UP followed, and an independent same-generation readback
observed Q-up. The terminal same-call result reported `recovered` and
`release_confirmed=true`; exact R11 fixture effect was saved, while runtime
`task_success` stayed null. The immutable audit remains FAIL_OR_UNKNOWN 17/19:
it counts an initial pre-admission `unknown_call` poll as a failure and the
immediate session close was busy while cleanup was draining. Processes and
fixture exited, hook and foreground cleanup passed. See the
[R11 result](../research/integration/win32_supervised_standard_caller_20261024_r11/RESULT.md).
The next one-shot should preserve the transient `unknown_call` and retry only
busy `interface_close` within a finite drain window.

**Standard-caller cancellation R10 (2026-10-24):** the one-shot public
stdio-MCP run again completed the fixture effect and independent same-generation
Q-up readback, but the 100 s hook gate expired about 0.780 s before injected
Q-down reached the hook (100.780 s after wait start; 103.483 s after hook
readiness). No cancel was sent; session close still reports release unknown.
The frozen audit is FAIL_OR_UNKNOWN 9/17. Across R06/R07/R09/R10 the Q-down
arrived 0.75–0.79 s after each finite hook wait, so the next test should poll
same-call results during the wait instead of extending it. Preserve R10 and do
not replay it; see its
[result](../research/integration/win32_supervised_standard_caller_20261024_r10/RESULT.md).
The goal remains active; no WSLc or Docker allocation was used.

**Standard-caller cancellation R09 (2026-10-24):** R09 preserved one public
stdio-MCP normal completion and exact fixture effect, but its 75 s cancellation
gate expired about 0.788 s before injected Q-down reached the owned hook
(75.788 s after gate start; 78.482 s after hook readiness). The frozen audit is
FAIL_OR_UNKNOWN 9/17; no public cancel was sent, session close did not confirm
release, and a separate same-generation readback later observed Q up. Do not
replay R09. See its [result](../research/integration/win32_supervised_standard_caller_20261024_r09/RESULT.md)
and raw. The next one-shot caller trial should use a 100 s finite hook-entry
gate and 180 s lease, preserving the hook/running/cancel ordering. No WSLc or
Docker allocation was used.

**Standard-caller cancellation follow-up (2026-10-24):** the new [R05
packet](../research/integration/win32_supervised_standard_caller_20261024_r05/README.md)
records a caller-teardown construction failure before native input. R06 and
R07 each returned a public zero-wait pending call ID and then completed the
owned fixture task normally, with an exact saved sentinel, verified empty
release, independent same-generation all-up readback, and clean foreground
restoration. They did **not** exercise cancellation: injected Q-down reached
the hook 10.7526 s after R06's 10 s wait and 45.7678 s after R07's 45 s wait,
after each finite hook gate had already been released. Both immutable packets
record FAIL_OR_UNKNOWN for the cancellation question; R05–R07 do not establish
public cancellation recovery. The [R06](../research/integration/win32_supervised_standard_caller_20261024_r06/README.md)
and [R07](../research/integration/win32_supervised_standard_caller_20261024_r07/README.md)
records preserve the delayed producer-start boundary. The next caller trial
must retain a finite window long enough to reach the hook, confirm the same
call is still running, then cancel once and verify exit-before-UP and
independent neutral state. The goal remains active; no WSLc or Docker allocation
was used.

**Supervised Win32 standard-caller effect path (2026-10-24):** the fresh [R04
packet](../research/integration/win32_supervised_standard_caller_20261024_r04/README.md)
passes its 15-check audit on the public stdio-MCP route. Observation and the
owned fixture share a target generation; one dispatch returned pending after
10.0028 s, and same-call readback showed `operation_invoked=true`,
`input_dispatched=true`, verified empty release, and completed action. An
independent neutral readback followed producer-exit confirmation, though both
timestamps rounded to the same monotonic tick. The exact fixture journal and
saved effect match, fixture cleanup restored the previous foreground, and the
session closed. Runtime task success remains `null`. R01's producer-directory
collision is repaired in `5da333c6`; R02's missing input-dispatch summary is
repaired in `a448064e`. R01 and R03 are preserved pre-effect failures: R01 hit
the path collision; R03 exceeded the public 10000 ms wait bound and was refused
before input. R02 independently passes a supplemental audit after its first
audit's pending-response assumption mis-scored the same-call terminal result.
Across this sequence, 84 related local tests pass in normal and optimized
Python. These results do not establish blocked-I/O release/recovery, a hard
deadline, atomic generation fencing, MAP01, integrated task success, matched
efficiency, or broad reliability. No WSLc/Docker allocation was used.

**Native Win32 low-level hook delay probe (2026-10-24):** the frozen one-run
[R01 packet](../research/integration/win32_sendinput_lowlevel_hook_20261024_r01/README.md)
delayed one injected F13 key-down in `WH_KEYBOARD_LL`. `SendInput` returned
0.9093 ms after callback return; one UP was observed, F13 was up, and unhook and
thread cleanup succeeded. The callback lasted 64.4284 ms against the predeclared
60 ms maximum, so the independent audit records **FAIL**. The one-shot raw,
conditions, source hashes, and audit are preserved. This supports the narrow
ordering observation for one finite callback stall only; it does not establish
a hard release deadline, indefinite-block recovery, public MCP recovery, MAP01,
or matched efficiency. Do not rerun this allocation.

**Native Win32 supervised recovery (2026-10-24):** the frozen [R03 packet](../research/integration/win32_native_supervised_sendinput_hook_20261024_r03/README.md)
passed all 20 predeclared audit checks in one owned EDIT fixture schedule. A
real F13 DOWN entered the injected `WH_KEYBOARD_LL` callback while its producer
was still inside `SendInput`; cancellation returned `pending` in 0.1971 ms,
the exact producer exited before recovery, and the prestarted helper performed
one same-generation `release_all` UP. An independent helper observed all-up
14.2328 ms after recovery began and again after the 1.5 s horizon. Cleanup
restored the previous foreground window, destroyed the fixture, retired all
children and closed the supervisor; emergency UP was unnecessary. The raw and
read-only audit are hash-bound. R01/R02 are preserved pre-action construction
aborts. This is one finite host/schedule and does not qualify the standard MCP
caller, task success, MAP01, bounded recovery across failure classes, efficiency
or broad reliability. Do not rerun this packet.

**Public Win32 overlap refusal (2026-10-24, synthetic):** the standard
`interface_guarded_win32_admit` endpoint now preserves the owner’s unresolved
producer refusal as a machine-readable `INPUT_PRODUCER_UNRESOLVED` result,
including the earlier operation ID. A public route regression confirms the
second action creates no call and never invokes another producer; replay and
task success remain false/unknown. The 57 selected public composition,
backend, owner and cancellation tests pass in normal and optimized Python.
This improves caller handling of the unresolved native operation but does not
prove native fencing or release. WSLc remains STOP/HOLD under #7924.

**Public Win32 effect and timing (2026-10-24):** R01 was refused before input
with `TARGET_GENERATION_REQUIRED`; its raw, audit, and clean fixture exit are
preserved. R02 forwarded the matching generation from public observe to the
standard dispatch and passed its 25-check audit with one exact independent
effect and verified release. R02 exposed a 15.625 ms GetTickCount64 resolution,
so its 78/141/94 ms endpoint readings are explicitly coarse. R03 uses the
100 ns QueryPerformanceCounter-backed `perf_counter_ns()` clock and also passed
25/25: click at 5.5515 ms, first/last text at 46.9063/60.5935 ms, effect file
close at 61.8722 ms, public response at 122.9508 ms, then independent readback
106.1251 ms after file close. See the
[R01](../research/integration/win32_public_mcp_effect_timing_20261024_r01/README.md),
[R02](../research/integration/win32_public_mcp_effect_timing_20261024_r02/README.md),
[R03](../research/integration/win32_public_mcp_effect_timing_20261024_r03/README.md),
[R04](../research/integration/win32_public_mcp_effect_timing_20261024_r04/README.md),
and [R05](../research/integration/win32_public_mcp_effect_timing_20261024_r05/README.md)
packets. This is one host/fixture positive path; release's exact sub-call time,
blocked-I/O release bounds, recovery, atomic generation fencing, MAP01,
matched efficiency, and broad reliability remain unproven. R03's 300 px final
image clipped the sentinel tail; R04's assumed 420 px width exceeded the actual
client area and failed at observe before input; both limits and the clean R04
UNKNOWN are preserved. R05 measures `GetClientRect`, uses the actual 404x181 client region,
and passes 29/29 with exact independent task effect, verified release, clean
fixture exit, and a retained screenshot showing all of `VISUAL-R05`. It records
dispatch-to-save at 59.7386 ms, public response at 129.0408 ms, and independent
readback 116.0156 ms after save close; see the R05 packet. This one positive
sample does not qualify blocked-I/O release, bounded recovery, MAP01, matched
efficiency, or broad reliability.

**Win32 unresolved producer fence (2026-10-24, synthetic):** while a direct
session dispatch is inside a synchronous input call, concurrent recovery and
overlapping dispatch now return `pending`/`INPUT_PRODUCER_UNRESOLVED` without
issuing UP or another producer. The [R01 packet](../research/integration/win32_inflight_recovery_fence_20261024_r01/README.md)
retains both accepted-before-return and blocked-before-acceptance fake-API
schedules; all 76 selected backend/session/MCP tests pass in normal and
optimized Python. After the fake producer resumes, its terminal UP/readback
returns the model to neutral and clears the deferred recovery request. This
narrows duplicate-producer and premature-recovery behavior in one session; it
does not interrupt a blocked native call, impose a hard release deadline,
qualify physical input or task effect, or use WSLc.

**Win32 public recovery-failure custody (2026-10-24, synthetic):** a new
public-MCP test injects a recovery helper that returns a mismatched operation
receipt. `interface_results` retains UNKNOWN, release confirmation/task success
stay unset, replay remains denied, the observer is not run, and the fake DOWN
state remains visible. Public admission also normalizes target-incarnation
property/read failures to `TARGET_GENERATION_CHANGED`; an explicit fake
`GetPropW` cookie fixed a test-fixture recursion through `ctypes.cast`. The
[R01 packet](../research/integration/win32_public_recovery_unknown_20261024_r01/README.md)
records the raw failure and repair plus 51 selected caller/backend/owner/
supervisor tests passing in normal and optimized Python. This verifies one
joined failure path only; native input, bounded physical release, live task
effect, MAP01, WSLc, matched efficiency, and reliability remain open.

**Win32 target-incarnation cookie lifecycle (2026-10-24):** production
`target_generation()` now adds a per-HWND-lifetime property and fails closed if
the property is denied, changed, or missing after binding. `close()` retains
the shared marker until Windows destroys the HWND, avoiding unsafe removal that
could invalidate another backend. The standard MCP session records backend
close receipts. A no-input native hidden-HWND probe passed with two backend
instances sharing the cookie and Windows removing it at HWND destruction; see
the [R04 packet](../research/integration/win32_target_incarnation_cookie_20261024_r04/README.md).
Two earlier setup failures remain in R01/R02, and the superseded removal design
is preserved in R03. The 79-test composed run passed in normal and optimized
Python. This does not
demonstrate numeric HWND reuse, cross-integrity behavior, an atomic check/use
fence, input/release, bounded recovery, MAP01, WSLc, efficiency, or reliability.

**Win32 target-incarnation property feasibility (2026-10-24):** the frozen [R01 packet](../research/integration/win32_property_cookie_20261024_r01/README.md) shows a same-integrity parent can `SetPropW` and read back a unique value on a hidden HWND owned by its child process. After destruction, the old handle was invalid and returned no property; a new HWND on the same PID/thread also had no value, but its numeric HWND differed, so reuse was not tested. The child exited cleanly and the 9/9 structural audit passes. Microsoft documents UIPI restrictions and per-window property cleanup requirements; this is a feasibility sample only, not a production generation fix or evidence for elevated targets, atomic fencing, input/release, recovery, MAP01, efficiency, or reliability.

**Native Win32 same-thread HWND allocation discriminator (2026-10-24):** the frozen [R02 packet](../research/integration/win32_hwnd_reuse_20261024_r02/README.md) created and destroyed two sequential cohorts of 256 hidden windows on one process/thread, using production owner-identity and `target_generation()` methods. All 512 windows were confirmed destroyed; no numeric HWND repeated across cohorts, so the result is `NO_HANDLE_REUSE_OBSERVED_IN_THIS_BATCH`. Its 10/10 structural audit passes. R01's pre-entry `advapi32` setup failure is separately preserved. This finite host-specific allocation pattern does not prove HWND reuse cannot occur or close the same-number alias, target-fencing, input/release, recovery, MAP01, WSLc, efficiency, or reliability gates.

**Public stdio MCP Win32 live integration (2026-10-23):** R01 failed before `session.dispatch` because Win32 lacked per-call capture-artifact support; preserve its raw failure. The repair now writes dependency-free PNG artifacts from exact BGRX capture; 28 focused tests and the 131-test CLI/API suite pass locally in normal and `-O` modes. Initial cross-platform CI exposed the missing Pillow dependency in the first implementation; the standard-library encoder fixes that failure. R02 confirmed the public observer creates a valid image artifact, then the probe failed while serializing the SDK image payload; raw is UNKNOWN and frozen. R03 independently reached public validation and one dispatch, and the fixture oracle confirmed click, exact 17-character text, and one save. The final release receipt remains `release_unverified` with unknown Ctrl/S and left-button states; R03 is a failed release trial and is not replayed. See the [R01](../research/integration/win32_public_mcp_live_effect_20261023_r01/README.md), [R02](../research/integration/win32_public_mcp_live_effect_20261023_r02/README.md), and [R03](../research/integration/win32_public_mcp_live_effect_20261023_r03/README.md) packets. This does not establish generation admission, bounded release under blocked I/O, supervisor recovery, MAP01, or efficiency.

**Native Windows target-identity smoke (2026-10-23):** the [R01 packet](../research/integration/win32_native_target_identity_20261023_r01/README.md) exercises production `Win32Backend.process_identity()` and `target_generation()` against one hidden HWND created and destroyed by the probe on this PC. The real Win32 API returned stable PID/process-creation identity and generation across repeated reads; the owned HWND was absent after destroy. Its 8-check raw audit and 12 focused tests in normal/`-O` modes pass. An initial import-path setup error is preserved. This qualifies only native identity API wiring for one live HWND; no input, release, target-reuse detection, task effect, recovery, WSLc, or efficiency claim.

**Native HWND reuse discriminator (2026-10-23):** the [R01 one-shot packet](../research/integration/win32_hwnd_reuse_20261023_r01/README.md) created and destroyed two hidden `STATIC` windows sequentially on the same thread, using production owner-identity and generation methods. Windows returned different numeric HWNDs (`50923368`, `50988904`), so the result is `NO_REUSE_OBSERVED_IN_THIS_SINGLE_TRIAL`; both windows were destroyed and the 7-check receipt audit passes. This is inconclusive about reuse/aliasing and was not retried. It adds no input, release, effect, recovery, MAP01, or efficiency qualification.

**Standard Win32 caller target-generation seam (2026-10-23, implementation commit `251f1182`):** read-only observation brackets capture with matching target-generation reads; standard API dispatch requires a matching `source.target_generations` value for each explicitly focused Win32 target. The full public observation receipt exposes the generation, and missing/malformed/stale values or effects without explicit focus refuse before `session.dispatch`; non-Win32 callers keep their existing path. Core-contract, observation, admission and public-MCP suites pass 67/67 normally and under `python -O`. The [native public-MCP R01 packet](../research/integration/win32_public_mcp_generation_fence_20261023_r01/README.md) passed 14/14 frozen checks: an observation token from one owned fixture process was refused by a new public caller configured for a distinct fixture process; public validation accepted the program, dispatch refused `TARGET_GENERATION_CHANGED` before input, and the independent fixture journal recorded no character input. Both fixtures exited cleanly. This closes that stale-process-generation caller gap for one sample, but leaves a post-check/use race and does not qualify accepted input, release deadlines, recovery, MAP01, WSLc, efficiency, or broad reliability.

**Real terminal saved-effect task (2026-10-23):** the [frozen rootless xterm trial](../research/integration/xterm_public_task_20261023_r01/README.md) uses public guarded MCP to type a known command through actual xterm/PTY/shell, producing exactly one independently read/fsynced record with owned ancestry.14 pre-frozen-auditor checks pass; source/native binaries and cleanup retained. Input returns65.438ms after invocation, saved effect commits72.876ms after invocation, so API completion precedes task commit by7.437ms in this sample. Custom record helper, one known zero-model task, no fault/comparison; no general terminal/Calc/MAP01 or efficiency/reliability claim. Setup is user-cache extraction only, not system installation or WSLc.

**Queued-UP boundary and interpretation correction (2026-10-23):** [two new frozen cases](../research/integration/x11_queued_up_cancel_20261023_r01/README.md) record target UP queued after the delayed XTEST request and before real sync. Without server pause: old counted task PASS/count1 and fresh PASS; with1000ms pause: old FAIL/count3, fresh PASS. Both preserve UNKNOWN/no replay and pass28 raw checks each. Earlier descriptions of the old task as an “explicit held-key” operation were incorrect: it is `key_chord`, stalled behind the injected delayed request. The new packet supersedes that interpretation without rewriting old raw/results. Completion-hold comparison #9427 remains valid for its distinct after-reply hook. No hard deadline, physical/MAP01, efficiency or reliability claim.

**Matched completion-hold discriminator (2026-10-23):** a [frozen ABBA public-guarded comparison](../research/integration/x11_tap_completion_hold_20261023_r01/README.md) uses identical current caller/guards with prior vs repaired key methods. During a one-second completion hold after a real X sync reply, both prior cases remain DOWN/count10; both repaired cases are UP/count1. All four end neutral; 47 pre-frozen-auditor checks pass. This qualifies that client-facing completion boundary only, not network reply loss, blocked send, stopped server, supervisor cancellation, general exactly-once effects, MAP01, efficiency or broad reliability.

**Single-key chord reply-boundary repair (2026-10-23):** the [backend repair](../research/integration/x11_single_tap_reply_boundary_20261023_r01/README.md) queues eligible single-key DOWN/UP before one final key-state reply, retaining subclass guards and possible-DOWN custody. 143 related pure tests pass normal/-O. A [fresh native public-caller run](../research/integration/x11_single_tap_live_20261023_r01/README.md) passes 24 raw checks and fresh count `[0]→[1]→[1]`; old explicit held-key count `[1]→[3]` remains task FAIL/UNKNOWN. This removes an avoidable reply wait, not stalled-write/queue atomicity or held-key repetition. No measured speedup, physical/MAP01, efficiency or reliability claim.

**Counted task-oracle repair and live verification (2026-10-23):** the [repair](../research/integration/xvfb_effect_count_oracle_20261023_r01/README.md) adds strict non-idempotent effect counts to the blocked-release fixture; 20 pure tests pass normally and under `-O`. A [new frozen native Xvfb run](../research/integration/xvfb_counted_effect_local_20261023_r01/README.md) independently reads old count `[1]→[4]` with unchanged value `[1]`, correctly scoring old task FAIL; fresh count `[0]→[1]→[1]` scores PASS. The 24-check raw audit and owned-process cleanup pass, while old runtime UNKNOWN/no-replay remains. This repairs observability, not old repeated effects or general exactly-once semantics. Other server-stop legacy scorers remain value-only; no WSLc/physical/MAP01, efficiency or reliability claim.

**Paused local caller trial and oracle counterexample (2026-10-23):** [R01](../research/integration/xvfb_blocked_release_local_20261023_r01/README.md) passed its single existing Xvfb test: cancel response 254.184 ms, post-resume all-up, fresh-target effect `[0]→[3]` with 89.901 ms input-to-independent-readback, old UNKNOWN/no-replay preserved. The separate 20-check raw audit also found three old-window KeyPress/effect handlers masked by idempotent `[1]` assignment, so the scorer's literal “one initial effect” is unproven/contradicted at event level. Next: explicit non-idempotent effect-count fixture/oracle and duplicate-event regression; preserve this result. Native WSL2 only, no WSLc/Docker or Windows desktop input; no efficiency/reliability/MAP01 claim.

**Local observation prerequisite (2026-10-23):** the [public MCP observation R01 packet](../research/integration/xvfb_public_observation_20261023_r01/README.md) records one new authenticated private Xvfb, two exact 64×64 fixture images, retained-image identity, timestamp ordering and clean close/exit; 19 offline raw-reconstruction checks pass. This qualifies the newly prepared local WSL2 observation environment only. No input, WSLc allocation, input-caused task effect or performance/reliability claim is made. Next: separately frozen blocked-I/O control/effect trial on a fresh owned server.

**Latest main checkpoint (2026-10-23, `b0dba32da`, PR #9420):** PR #9418 integrated the synthetic Win32 caller and custody fixes; #9419 added oracle timestamp-window validation; #9420 repaired private-Xvfb pause cleanup using a retained process descriptor and post-STOP exception cleanup. Their packets preserve local test scopes and failures. Native input/release, live task/MAP01 effect, recovery authority, matched efficiency and reliability remain open.

**Win32 target-generation discriminator (2026-10-23, PR #9435/#9436 and thread-identity follow-up):** `Win32Backend.target_generation()` hashes the configured HWND, GUI-thread ID, owner PID, and process creation time; the reader rechecks both PID and thread ID across the process-time query. The adapter and `create_server()` public-MCP tests confirm a changed HWND or GUI thread within one process is rejected before operation creation or producer start. All 25 focused backend/caller/server tests pass normally and under `python -O`. This is mocked Win32 API composition; reuse of the same numeric HWND on the same thread can still alias, native input remains unqualified, and no WSLc allocation was used.

**Valid-generation public Win32 input, release, and fixture task effect (2026-10-23):** [R04](../research/integration/win32_public_mcp_valid_generation_effect_20261023_r04/README.md) used the actual stdio-MCP caller on the user-authorized PC and one owned Win32 fixture. Public observation returned a generation matching the fixture's native owner identity; validation accepted the matching program; one dispatch completed with a verified empty release receipt; the fixture independently saved the exact requested sentinel and journaled 18 character records plus one save event. The pre-frozen audit passes 14/14 and the fixture exited cleanly. This is one local fixture task/effect sample; R01/R02 setup failures and R03's frozen expectation mismatch remain separately retained. No blocked-I/O recovery, hard release deadline, post-focus race, MAP01, WSLc, efficiency or broad reliability claim is made.

**Win32 runtime post-admission generation guard (2026-10-23):** the standard backend now re-reads a focused target's generation before focus, immediately after focus, and before every target-specific operation when the program carries `source.target_generations`. A changed/unavailable generation raises a fail-closed execution error and uses the existing release path; programs without generation evidence keep their legacy behavior. Five regression cases cover stale-before-focus, change-during-focus, change-between-effects, matching operation, and legacy operation. Win32 backend tests pass 73/73 in normal and optimized Python; relevant public caller tests pass 31/31 in both modes. This narrows the admission-to-use window but is not an atomic OS-side fence, does not interrupt a blocked generation query or platform call, and does not prove bounded release or task success.

**Post-admission guard live compatibility R05 (2026-10-23):** the [one-shot packet](../research/integration/win32_public_mcp_valid_generation_effect_20261023_r05/README.md) ran one actual public stdio-MCP observe/validate/dispatch against a fresh owned Win32 fixture on the user-authorized PC, pinned to main `b9a8678b15fc2a271928a9f3b1429e396bdb23dc`. The observed generation matched the native owner identity; the exact frozen program was accepted; one dispatch completed with a verified empty release receipt; the independent fixture oracle saved the exact sentinel and journal; the process exited cleanly. The frozen audit passes 14/14 and raw is hash-manifested. This is one stable-generation positive-path compatibility sample. It does not observe an adversarial native generation change between focus and input or prove bounded release, recovery, MAP01, efficiency, or broad reliability.

**WSLc smoke bounded-call repair (2026-10-23, PR #9438):** current main includes merged PR #8503's exact-container cleanup query, but its WSL/WSLc subprocesses had no caller timeout and its `finally` block deleted receipts even when run/cleanup state was unknown. The smoke now bounds version/run/cleanup CLI waits at 10/90/15 seconds, kills only its own timed-out CLI process, retains the unique probe directory and raw stdout/stderr logs after any run/cleanup uncertainty, and returns UNKNOWN without retry. PowerShell parser and child exit/output/timeout tests pass; an offline fake-CLI smoke passes success cleanup, run failure, run timeout, cleanup timeout, and non-empty cleanup retention. No WSLc CLI, container, image, or Docker command was run; #7924 remains STOP/HOLD.

**Local Linux process-only result:** the [R02 packet](../research/integration/xvfb_pidfd_live_20261023_r02/README.md) records one owned Xvfb and three predeclared schedules passing with actual Linux pidfd STOP/CONT calls. Independent observers found healthy stopped/resumed states and resumed states after injected status-read/timer-start faults; target exit and absence were confirmed. The [R01 readiness FAIL](../research/integration/xvfb_pidfd_live_20261023_r01/README.md) is unchanged. R02 uses process-state readiness, not X transport readiness. No GUI input or WSLc operation occurred; this qualifies only this helper process-control sample, not live input release/task effects.

**Oracle observation-window follow-up (`79aa55c0d`):** the [timing packet](../research/integration/win32_oracle_timing_20261023_r01/README.md) reproduces two false successes with stale/future observation timestamps. The caller now requires observation time within the oracle reservation/receipt-processing window and retains both endpoints. All 27 related tests pass normally and under `-O`, including valid endpoint equality and immutable UNKNOWN after rejection. This validates timestamp consistency; it does not independently establish task effect or effect latency.

**Local Win32 supervisor checkpoint (2026-10-23, branch `codex/win32-supervisor-implementation-plan`, `4121be229`):** the approved prestarted-helper model now starts and validates recovery/observer workers before operation admission, then reuses them with operation-scoped result and completion receipts. Public route regressions cover duplicate start/cancel, blocked observation, timeout followed by a late oracle receipt, and separate Generation-A/Generation-B accounting. A fake-API spawned-process test invokes the actual `Win32RuntimeSession` and `Win32Backend.execute()` through blocked-before-acceptance and accepted-before-return schedules; both record producer retirement before recovery UP. A retirement timeout stays UNKNOWN with no recovery UP. The R01 [custody packet](../research/integration/win32_supervisor_custody_20261023_r01/README.md) records 79/79 selected pure/fake tests passing in normal and optimized modes and includes raw output, conditions and source hashes. This branch does not qualify native Windows input, physical release, late-DOWN exclusion, a live task/MAP01 oracle, hard real-time bounds, matched efficiency, or repeated reliability. An earlier broad command accidentally ran the native fixture integration class and failed before a successful emission was recorded; a fixture process query afterward found no remaining process, but this is retained as an unqualified incident because the run does not exclude all native API calls or side effects. Do not rerun that class. No WSLc allocation or Docker was used; #7924 remains STOP/HOLD.

**Joined Win32 caller/backend checkpoint (2026-10-23, `de457b73e`):** the [joined-path R01 packet](../research/integration/win32_public_backend_composition_20261023_r01/README.md) connects public MCP tools to the actual Win32 session/backend through the existing injected producer factory with an inert API. Three new cases cover both blocked-DOWN schedules and unconfirmed producer retirement; all 15 related tests pass normally and under `-O`. An intentionally premature fake UP fails the ordering check. This closes a synthetic test-composition gap; production native adapter, real target identity, physical release, live task effect, efficiency and reliability remain open.

**Current-main Win32 synthetic recheck (2026-10-23, `4c0fe4d31`):** the additive [R02 packet](../research/integration/win32_public_backend_composition_currentmain_20261023_r02/README.md) reruns 48 public-caller, backend-composition, owner, and recovery tests in normal and optimized Python against the current-main tree. Its eight retained public-backend traces pass an independent audit for generation/operation binding, one producer attempt, retirement-before-recovery ordering, UNKNOWN retention, and separate task-effect state. The traces still use inert Win32 APIs; native release, live task effect, WSLc, matched efficiency, and reliability remain unqualified.

**Win32 start-generation repair (2026-10-23, `d06b5d280`):** the [recheck packet](../research/integration/win32_start_generation_recheck_20261023_r01/README.md) reproduces stale/unavailable target generations incorrectly authorizing a producer after admission. The caller now rechecks before factory work and before gate authorization, retains UNKNOWN on failure, and retires a still-gated child without requesting compensating input. Five pre-fix cases fail as expected; 43 related tests pass normally and under `-O`, including cancellation during a blocked generation query. Atomic native target fencing and recovery-time target authority remain open.

**Closed-gate cancellation repair (2026-10-23, `aa891d55f`):** the [new packet](../research/integration/win32_unopened_gate_cancel_20261023_r01/README.md) reproduces an unwanted recovery UP while the final generation query was blocked and the producer gate was still closed. The public caller now declares the gate requirement, and the owner refuses recovery after retiring a never-authorized child. The fixed trace contains only child exit; UNKNOWN/no replay is retained. All 112 focused and compatibility tests pass normally and under `-O`. This is a synthetic-only repair, not native release qualification.

The X11 supervisor remains opt-in. Public-caller live-Xvfb bystander refusal has one scoped test-wrapper sample. For current local Win32 evidence and limits, use the dated checkpoints above and the [supervisor design and qualification record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md) and [Win32 operation-owner implementation plan](architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md).

**Prior checkpoint before PR #9408:**

**Repository checkpoint (2026-10-22, historical):** PR #9401 is merged at
`b688ecd3fdb4726b59201f10753ca65d82942b2b`; it preserves the scoped r09
Chromium/App Server polling packet with an explicit source-currency limit. PR
#9402 at `4606c917d22b0da0bd42cdbe7b95fbe606053f5e` records that no complete
r09 source snapshot exists across 48 linked worktrees. PR #9403 at
`375682310fa29d3bd0bf2af71835ef36ab3dc8ac` adds the Win32 operation-owner
plan and confirms the existing owned-process recovery path is X11-specific.
PR #9400 at `632d3603a8df157c1e841dac7ca422c766c77e60` adds a worktree-custody
report. These changes do not alter runtime behavior or the r151 queue
membership. The
user-selected prestarted-supervisor design is already documented in the
canonical [design and qualification record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md);
it remains opt-in and unqualified at the limits recorded there. The current
organization plan continues from that design and the [worktree custody
report](maintenance/worktree-custody-recheck-20261022-r01.md). A read-only
recheck of the r09 Chromium packet found 316/317 artifact hashes matching
(README changed after its retained audit); all 309 r09 raw files match. Of the
179 frozen source files, 161 match the extant dirty source worktree. A
read-only search across all 48 linked worktrees found no complete source
snapshot: expected versions for 170/179 entries occur somewhere, while nine
were not found. The source worktree remains untouched.

The current Win32 safety follow-up has a separately reviewed
[operation-owner implementation plan](architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md)
and an [inert prototype packet](../research/integration/win32_operation_owner_prototype_20261022_r01/README.md).
Its r02 synthetic suite passes 12/12 normally and under `-O`; r01's one
expectation failure is retained. The prototype confirms only its own process
ordering. It makes no Windows `SendInput`, physical-release, standard-caller,
or task-success claim; native work remains gated, and #7924 remains STOP.

PR #9404 is merged at `a8f504597ef6a8e097e93dd1cf64611030eea9f7` and retains
the Phase 1 Win32 process-owner model, including the r01 failure and r02
12/12 synthetic pass in normal and optimized mode. A subsequent Phase 2
prerequisite adds a digest of owner PID plus process creation time to the
private Win32 move-reference binding and refuses when identity is missing or
changes before input; related Win32 suites pass locally in both modes. This
still does not connect the owner to the public standard MCP caller:
`mcp_server` has no guarded-Win32 route, and the private MoveBridge remains
synchronous. Bounded release under blocked native I/O, public caller
composition, independent task effect, matched efficiency and reliability
remain open. No native input or WSLc allocation was used; #7924 is OPEN/STOP.

**Current verified functional baseline (2026-10-22):** PR #9397 merged at `b0e8c6c9b4cfb7917932f52e7a69d8267348aa89`, #9398 at `b57e140848087ab814db874f7dfe410926afd387`, and #9399 at current main `08064035460187ba5c8c5cbb2f4e9732ca622ada`. The fresh r151 membership recheck at that SHA has 1,654 open Issues and 452 open PRs, exactly matching r150. PR #9397 adds a public-caller test for terminal receipt archival blocked after cancellation; its scope and limits are in the [supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md). Latest runtime behavior remains the bounded MCP-relay cancellation read-ahead from PR #9389, with one deferred ordinary request, one reserved response and fail-closed later dispatch; its relay/Fake X composition suites passed 26/26 in normal and optimized Windows CPython 3.11. PR #9395 adds offline App Server usage reconciliation checks (44/44 related tests in both modes on its exact main source). These are synthetic/local evidence; production provider routing, external usage reconciliation, native/physical release, live MAP01 effect, matched efficiency and broad reliability remain open. PR #8800 remains on an A14 raw-custody hold: its public aggregate is preserved, but the original private report/protocol/images and their owner were not recoverable in the accessible workspace; no rerun was made. The linked-worktree review found 48 worktrees, 14 with changes, including two with thousands of changed entries and unresolved ownership; see the [custody report](maintenance/worktree-custody-recheck-20261022-r01.md). WSLc Issue #7924 remains OPEN/STOP. See [r151](maintenance/repository-inventory-recheck-20261022-r151.md) and the [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md); cleanup and consolidation records retain historical receipts.

## Historical evidence summaries

PR #9377 adds a research bridge from the existing model-call signature to the provider-attempt ledger and standard public MCP caller. Its injected-model tests preserve wrapper inputs, turn-level usage and JSONL, refuse a stale generation, and retain partial JSONL on timeout without sending a tool call. This is contract/composition evidence only: no real provider run or independent usage-log reconciliation occurred, and #57 remains open.

The active objective is computer control: preserve model-led intent and strategy while qualifying bounded local observation, input release, task-effect checking, and recovery. PR #9346 integrated the retained R02 evidence at `4fd2fe76b516844c89efc2e3fb044dff6ceec5bc`; that Xvfb run used source `cdc8bd6b65bf976137db645c2be31e20090f7d67`. See its packet for the exact historical conditions. Use the [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md) as the current execution pointer; the [cleanup ledger](REPOSITORY_CLEANUP_PLAN.md) and [consolidation record](REPOSITORY_CONSOLIDATION.md) retain historical receipts and must not be treated as live ownership grants.

Historical current-main addendum after PR #9362 (`df2b41e4a4e0ff03a3a7a139416003bd5599b16`): the [Win32 blocked-SendInput R01 packet](../research/integration/win32_blocked_sendinput_recovery_20261022_r01/README.md) exercises that source's synchronous backend with an inert fake that accepts CTRL-down and blocks before returning. Recovery refuses with no UP while modeled key state remains down; normal and optimized CPython agree. This does not show Windows blocks at that point or establish physical release. The r138 membership pointer and PR #9363 status below applied to that historical checkpoint only; see r146 and the live repository plan above for current cleanup status.

The existing [golden desktop v3 run](../runtime/GOLDEN_DESKTOP_DEMO_V3.md) is a separate real-model integration candidate: one Codex app-server grounding thread completed two image-grounding turns plus one schema preflight; six fixed tasks completed exact-once, all 57 terminal programs verified neutral input, and the old-target pointer was never admitted. Its usage and timing are one persistent-only allocation with only descriptive comparison to retained v1, not a matched public-MCP comparison or reliability estimate. The 232-file/13,805,562-byte retention manifest matches current-main Git blobs. Re-running its source auditor against current main fails its frozen source-hash precondition; this is not a new experiment failure and does not replace the retained outcome. This path shows that a real model-backed desktop route exists. PR #9377 adds a research wrapper bridge, but production model-runner routing, independent provider usage reconciliation, and an integrated live comparison remain open.

Historical membership receipt [r138](maintenance/repository-inventory-recheck-20261022-r138.md) captured main `5a32f1e486b40103a1f24a6059ae78c8cb884e0f` with 1,655 open Issues and 457 open PRs; it is superseded for membership by [r151](maintenance/repository-inventory-recheck-20261022-r151.md). Counts and hashes establish membership only, not semantic disposition. Refresh every live record before changing its state. See the [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md) for the current execution order and the [cleanup ledger](REPOSITORY_CLEANUP_PLAN.md) for historical queue receipts.

The opt-in prestarted supervisor has two retained current-main WSL2/Xvfb outcomes. R02 passed one standard-caller trial at source `cdc8bd6b65bf976137db645c2be31e20090f7d67`; R03 is an independent repeat at source `6b276fcabfa11c060282e0714501a1057e75c0a6`, merged by PR #9351. Both measured caller admission-to-response below 300 ms, independent key-up readback, and distinct fresh-session synthetic task-oracle success through an 8.5 s horizon; neither promotes the canceled operation from `UNKNOWN`, sets runtime task success, or permits replay. Their separate packets preserve raw conditions and source identity.

A test-only R01 packet then stopped its exact private Xvfb process for 1,500.674 ms. The standard caller returned `pending` 253.566 ms after cancellation admission while Xvfb remained stopped; after resume, supervisor release readback completed in 59.355 ms and an independent client saw all keys up in 98.039 ms. The fresh synthetic task oracle passed, while the old cancellation remained `UNKNOWN` and replay-denied. See the [R01 boundary packet](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01/README.md) and [design record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md). It does not establish release while X11 is stopped, physical desktop/MAP01, matched efficiency, or reliability.


A matched private-Xvfb pilot then ran three no-pause controls and three 1.5 s whole-process pauses on current main `cc5ef16c560cc985ee0951d3d53d659e892f5167`. All six passed the frozen admission-based composite; response ranged 253.263–256.398 ms, and pause-arm independent all-up readback followed resume by 101.874–127.834 ms. Its pre-call harness timestamp includes test setup and a deliberate 50 ms stop-confirmation wait, so actual caller invocation-to-return is unqualified. The synthetic effect oracle passed but exact effect-readback time was not recorded. See the [matched pilot packet](../research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/README.md); this is three pairs, not broad reliability or efficiency evidence.

The corrected caller/effect timing instrumentation then passed one unpaused WSL2 private-Xvfb trial on the PR #9354 code. It measured cancellation invocation-to-return at 95.283 ms, input-to-app-event at 37.701 ms, event-to-effect-commit at 0.097 ms, commit-to-independent-readback at 4.937 ms, and input-to-readback at 42.735 ms. The separate synthetic task oracle passed, while the prior cancellation remained UNKNOWN and replay-denied. The [R01 packet](../research/integration/standard_caller_xvfb_current_main_20261022/caller-effect-timing-r01/README.md) preserves raw output, conditions and a PowerShell reconstruction. The outer WSL wrapper returned 1 even on a no-op command; the test subprocess itself returned 0. This is one unpaused synthetic observation, not a matched estimate, broad reliability result, or WSLc evidence.

On exact current main `1263068ac473d6e64bad2136282fcfbf9eab666d`, a clean-worktree local recheck passes 63 supervisor/owned-caller/server-stop tests (one skipped) and 33 ledger/provider-recorder/public-MCP tests in both normal and optimized Python. The [R03 packet](../research/integration/standard_mcp_task_ledger_57_v1/current-main-20261022-r03-local-recheck/README.md) preserves raw output, exit codes, conditions, and source blob IDs. The composed target-generation refusal uses an injected fake provider and the public compiled MCP endpoint. A scoped source search found no matching production provider call site in `runtime`; external usage reconciliation and live-provider task effect remain open.

The supervisor design also retains an open authority gap: the current per-method input lease does not exclude competing X11 clients from global key/button state. Owner-PID absence or supervisor-PID reuse is not sufficient authority for a shared-desktop XTest release. Until an exclusive-input lease is represented and checked, shared-desktop release remains unqualified; see the [design note](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md).

## Current live-XRes bystander result (2026-10-22)

The direct-worker private-Xvfb R01 result remains preserved in its [disposition](../research/integration/live_xres_bystander_reuse_20261022_r01/DISPOSITION.md); R01 of the public-caller packet is separately retained as a preflight-only failure. The later public-caller [R02 disposition](../research/integration/live_xres_public_caller_bystander_20261022_r02/DISPOSITION.md) records one scoped live-Xvfb refusal: natural base reuse, independent PID observation, no release attempt, public result UNKNOWN/no-replay, and independent key-up readback after the delayed horizon. Its audit and source hashes pass. The response time of 251.602 ms is a single descriptive observation, not a hard-bound or reliability estimate. No WSLc/Docker allocation was used.

The public-caller Fake X regression passes in normal and optimized modes; the live-Xvfb caller composition has one scoped pass using a test-only bystander wrapper. It does not prove global input exclusivity. No WSLc allocation is verified; this work used Ubuntu WSL2 only and made no WSLc or Docker operation. Matched efficiency, physical desktop control, MAP01, WSLc portability, and broad reliability remain unqualified. The repository records #17 and #57 as open and #7924 as STOP/HOLD; refresh each live record before any disposition.

On current main `4bcf4e0a9254a8434032e00f6c4965e72c13293d`, a local public-caller target-generation regression recheck passed 20/20 in normal and optimized CPython 3.11.9. It includes fresh-session recovery with the prior UNKNOWN cancellation receipt retained. The adversarial lifecycle check/use race still permits a bounded prefix press after the final local check; the caller then verifies release and refuses retry. This is current-source Fake X evidence, not atomic generation validation or live X11/task-success evidence. See the additive [current-main recheck packet](../research/integration/standard_caller_target_generation_regression_20261022_r01/current-main-20261022-r01/README.md).

X.Org's XTEST protocol accepts a no-delay/relative-millisecond input time, while Xlib `XSync` waits for server processing and X11 has no cross-client request ordering guarantee. This source-backed inference means helper termination bounds caller waiting but does not prove an already accepted request cannot take effect after a deadline. Release-effect bounds during X11 unavailability remain unproven; see the [deadline semantics audit](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#xtest-deadline-semantics-source-audit-2026-10-22). No WSLc allocation was used.
The merged [PR #7181 P01 report](../research/audits/native_three_arm_57_p01_5884_20261004/REPORT.md) is a real three-arm native comparison: persistent input+output was 39,329 tokens versus 109,373 plain and 111,226 ephemeral; ready-to-independent-oracle time was 27.712, 36.631 and 46.550 seconds, respectively. It records 18 independently checked effects and one bounded persistent-path repair. Keep its disposition at HOLD: one fixed-order six-task sample per arm on one known fixture/domain, with model/cache/host-load confounding and limited timing scope. This contributes measured evidence to #57 but does not satisfy the integrated current-caller, second-domain or broad efficiency/reliability gates.

The [r51 navigation coverage audit](maintenance/idea-index-coverage-20261019-r51.md) splits 491 missing primary rows into 20 disjoint discovery batches; it does not classify meaning. See the [repository consolidation plan](REPOSITORY_CONSOLIDATION.md) for family-by-family review and disposition criteria. The first current semantic audit refreshed #6 and #56 against their live Issue records and found the existing [family entry](ideas/reactive-macro-symbolic-interface.md) accurate; both distinct research questions remain open. This page is the short entry point, not an experiment ledger.
The dated [worker dispatch r01](maintenance/worker-dispatch-20261019-r01.md)
records three disjoint family candidates (#17, #5, #59), not current assignments
or resource grants. #17's local Fake X packet is complete. The #5 Fake X
check/use discriminator is now preserved in
[its packet](../research/integration/fake_x_window_lifecycle_check_use_20261019/README.md):
one press can occur after the lifecycle reader retires in the constructed
schedule, followed by refusal and verified Fake X prefix release. This does not
qualify live X ordering or physical release. #59 and every reused work packet
still require live source/owner refresh. Shared indexes remain serially
integrated.

## Objective

Solve computer control: keep intent and strategy with the capable model; use
bounded local observation, input, verification and recovery where they preserve
correctness and reduce waiting, model calls or total resources. Universal
computer control remains available. No component PASS proves the full objective.

## Current maintainer priority

Organize the repository so many workers can find useful, independent work and
deliver it without conflicting instructions, duplicate experiments or lost
evidence. Organize ideas into hypotheses, existing results, dependencies,
priorities and executed tests. Documentation or Issue closure alone does not
resolve a research question. Existing finite/running work keeps its safe boundary.
Use the concise [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md)
for the current work order; the cleanup ledger and consolidation record remain
the detailed historical receipts.
Repository cleanliness means every active artifact has a traceable disposition,
not that all Issues are closed; see the [current consolidation plan](REPOSITORY_CONSOLIDATION.md#repository-wide-organization-plan-preserve-ideas-enable-parallel-work) and its detailed [family-by-family disposition rules](REPOSITORY_CONSOLIDATION.md#実行計画-r26--アイデアを保全した全体収束).
The first current semantic triage keeps broad reactive-control Issue #6 distinct
from focused symbolic-interface Issue #56; its exact next audit is recorded in
the [family entry](ideas/reactive-macro-symbolic-interface.md) and [work map](WORKER_WORK_MAP.md).
The visual-interface family now separately maps the #4 north star, #3 grid, #5
address/feedback contracts, #7 view-set selection and #8 composite packing; its
finite #7 crosswalk and evidence limits are in the [family agenda](ideas/visual-interface-agenda.md).

The [A02/A03 evidence note](../research/integration/standard_caller_blocked_x11_release_20261019/README.md)
preserves both consumed first outcomes: A02 stopped before probe entry on an
incomplete source mount; A03 passed one healthy control but timed out before
the held-reply predicate. Do not replay them. The offline stream parser has
since been connected to test-only relay/caller composition in merged PRs #9136
and #9153. Local Fake X tests now exercise blocked reply, cancellation,
disconnect, child retirement and a synthetic late queued KeyPress after an
injected separate empty readback. The caller remains `UNKNOWN` and does not
claim task success or permit replay; see the [preserved late-down packet](../research/integration/standard_caller_fake_x_relay_20261019/late-down-after-release-counterexample-20261019-r01/README.md).
The synthetic protocol order is modeled, not live server evidence. A later
[X11 server-ordering source audit](../research/integration/standard_caller_fake_x_relay_20261019/server_disconnect_order_audit_20261019_r01/README.md)
keeps the injected late-down result intact while marking that ordering
unverified; it isolates an XTEST delayed-request case for a version-pinned
Xvfb check. The
additive [same-PID two-connection relay discriminator](../research/integration/offline_proxy_reply_framing_20261019/two-connection-r01/README.md)
forwards a colliding-sequence identity reply while holding only the matching
input reply; parser/relay tests pass 28/28 and standard caller relay composition
passes 3/3 in normal and optimized Python. The standard caller exercises its
identity-query worker through the real target-query and process-identity logic,
backed by shaped synthetic XRes/PID replies; the socket relay carries related
synthetic transaction markers over a second connection. That worker sends
three synthetic request/reply transactions across the second relay before
input. The fixture generation-change case now rejects stale evidence before
either relay sees a KeyPress. It does not exercise XRes wire encoding or live
PID discovery. A03's missing per-connection trace and original failure are
unchanged. Two separate native WSL/Xvfb validations are now retained:
[blocked-I/O release and liveness timestamp](../research/integration/standard_caller_xvfb_blocked_release_20261020/local-native-wsl-r01/README.md)
and [standard-caller target generation and recovery](../research/integration/standard_caller_xvfb_blocked_release_20261020/local-native-wsl-generation-r03/README.md).
They exercise the Linux caller against private synthetic Xvfb applications;
they are not WSLc portability, physical desktop, or MAP01 evidence. The
separate [Windows-host generation/cancellation recheck](../research/integration/standard_caller_windows_generation_cancel_recheck_20261021/README.md)
passes three Fake X standard-caller tests in normal and optimized Python;
stale process/window generations are refused and blocked-owner cancellation
retains UNKNOWN. It does not qualify a live X server, physical input, or task
effect. The [Windows process-start probe](../research/integration/standard_caller_cancel_process_start_20261021/README.md)
measures synchronous event-loop stalls during actual helper startup and
preserves the release gate after unknown disconnect.
The [event-loop cleanup-delay probe](../research/integration/standard_caller_cancel_eventloop_block_20261021/README.md)
separates those injected cleanup waits from real process-start delay; the
[prestarted-supervisor Fake X probe](../research/integration/prestarted_supervisor_fakex_feasibility_20261021/README.md)
is construction feasibility only and does not validate production supervisor
behavior.
The [standard-caller duplicate-cancel retention characterization](../research/integration/standard_caller_duplicate_cancel_retention_20261021/README.md)
compares that production-caller seam with the already-passed independent-owner
duplicate-cancel result in Issue #814: one cleanup attempt occurred, but the
duplicate returned `not_active`, no operation ID or retained cancellation
record was exposed, and the action result remained UNKNOWN. It is one Fake X
trial, not a release guarantee.
The [prestarted cancellation supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
records the merged opt-in caller path, XRes reuse rule, retained standard-caller
Xvfb outcome, and remaining qualification gates. Its response/transaction
budgets remain experimental targets, not compatibility promises.
The local [public MCP cancellation-operation packet](../research/integration/public_mcp_cancel_operation_registry_20261021/README.md)
now implements one operation ID per call, a dedicated one-worker cancel path,
pending/terminal retention alongside (not inside) the action result, and a
450 ms Fake X caller-response check. Its normal and optimized focused suites
pass 77/77 each. It still has no whole-transaction deadline or prestarted
cleanup process and does not qualify real X11 release, task effect, recovery,
or WSLc.
The [current-main shutdown/cancel-drain probe](../research/integration/standard_caller_shutdown_cancel_drain_20261022/README.md)
found that server lifespan exit stays pending after owner close returns while a
cancellation callback remains blocked; the retained owner-liveness snapshot was
stale against a Win32 PID readback. This is a test-gated Windows Fake X result,
not real X11 release or a general shutdown-time guarantee.
Current-source native-WSL/Xvfb reruns now directly cover two remaining caller
boundaries: [blocked-owner release and delayed-request horizon](../research/integration/standard_caller_xvfb_blocked_release_current_e7_20261021/README.md)
independently observed XTEST keys up in 448 ms while the public caller retained
UNKNOWN; [target-generation/recovery/effect](../research/integration/standard_caller_xvfb_generation_current_e7_20261021/README.md)
refused stale input, recovered in 10 ms, and verified a synthetic application
effect through an independent X client. Both run current source `e7d79d04`,
one trial each, on responsive private Xvfb. Neither covers a stopped X server,
physical desktop, MAP01, reliability population, or matched efficiency.
separate generation-run r01/r02 prelaunch stops are preserved without test
retries. WSLc Issue #7924 remains `STOP / HOLD` for shared ownership; no WSLc
allocation is verified. A future shared WSLc/MAP01 run requires fresh
allocation and ownership evidence. Further local tests should target a concrete
caller/integration decision rather than copy existing parser-only fixtures.
The additive [standard-caller target-generation regression packet](../research/integration/standard_caller_target_generation_regression_20261022_r01/README.md)
records five Fake X caller/lifecycle cases passing in normal and optimized
Windows CPython 3.11.9 at source `c5fd95f38d1e4a780ea0c934da7103dafc3b5e8a`.
It preserves an adversarial destroy-gap schedule where a key prefix can be
emitted after the last local check, then released and locally verified; this
does not make capture-to-press atomic or establish live target generation.

Start with [Worker Quickstart](WORKER_QUICKSTART.md), then select a bounded item
from the [worker work map](WORKER_WORK_MAP.md). The map suggests work; it does not
assign people, grant resources or replace current user instructions.

## Win32 R24 fresh-generation result (2026-10-24)

The additive [R24 packet](../research/integration/win32_supervised_standard_caller_20261024_r24/RESULT.md)
tested one new supervised stdio-MCP session and target generation after R23.
The independent fixture effect was exact, and the persisted runtime report
records completed execution, verified all-up release, producer exit, and
neutral readback. The public dispatch nevertheless returned `pending` at
8,004 ms; the immediate close returned `busy` with release unconfirmed. The
session close later recorded `closed` but still `release_confirmed=false`.
Strict R24 outcome remains `FAIL_OR_UNKNOWN`; the persisted result only narrows
the failure to caller response/close timing. The raw's release timestamp
annotation is contradicted by the persisted receipt and is rejected in the
additive audit. A new attempt should wait longer than the observed 8.886 s
producer completion and record the actual terminal receipt. R23's separate
raw/manifest hash discrepancy remains an explicit preflight limitation.

The separate [R25 result](../research/integration/win32_supervised_standard_caller_20261024_r25/RESULT.md)
stopped before input: the public caller rejected `wait_for_result_ms=12000`
with `INVALID_RESPONSE_WAIT` and `operation_invoked=false`. The source caps
this wait at 10,000 ms. R25 used a new fixture and generation, wrote no effect,
and cleaned up normally. R26 uses the supported 10,000 ms maximum in a fresh
session; no R24 or R25 action is replayed.

R26 used the supported 10,000 ms response wait but still returned `pending`
at 10,010.6 ms. Its independent effect completed at 10,835.7 ms; the persisted
report later records all-up release at 10,852.9 ms and neutral producer-exit
readback at 10,915.9 ms. Public close returned `busy`, while later session
shutdown reported closed without release confirmation. The strict result is
`FAIL_OR_UNKNOWN`; an additive audit verified the persisted effect/release
without changing that outcome. R27 will follow the pending receipt with
bounded read-only `interface_results(call_id)` retrieval before closing.

R27 follows that protocol and passes 14/14: after the 10 s public dispatch
returned `pending`, six read-only lookups of its exact call ID produced the
terminal `completed` receipt at 11,059.7 ms from dispatch start. The receipt
records verified all-up release at 10,818.8 ms, producer exit and neutral
readback; the independent fixture effect and event journal match exactly. The
public session closed, fixture exited cleanly, and foreground was restored.
`interface_close` itself says `release_confirmed=false`; the separate terminal
dispatch receipt provides the release evidence. This is one local Windows
fixture trial, with no WSLc, MAP01, blocked-I/O release, matched efficiency, or
broad-reliability claim. See the [R27 packet](../research/integration/win32_supervised_standard_caller_20261024_r27/RESULT.md).

## Remaining scientific gates

The release-supervision packet preserves main run [39444638512](https://github.com/Unjuno/agent-interface/actions/runs/39444638512), instrumented run [39446039020](https://github.com/Unjuno/agent-interface/actions/runs/39446039020), rebased-head failure [39447636867](https://github.com/Unjuno/agent-interface/actions/runs/39447636867), and fixture-fixed rerun [39448218110](https://github.com/Unjuno/agent-interface/actions/runs/39448218110). r01 retained two `worker_did_not_exit_cleanly` failures among four cancel-retirement comparisons; its receipts discarded child result status. The supervisor diagnostics preserve status and monotonic receipt/exit times while leaving forced termination `UNKNOWN`. r02 had five blocked-owner cases with independent release readback and synthetic-oracle PASS; release took 337–411 ms and cancel 390–654 ms. In r04, all five blocked-owner oracle checks passed (cancel 628–879 ms; release-worker 549–570 ms), with release `UNKNOWN`, runtime `task_success=null`, replay denied. The r03 fixture race was fixed by atomic marker publication and the full Xvfb workflow passed; r03 remains preserved as failure. The separate whole-server-stop task oracle also failed. These results do not establish release while platform I/O is unavailable, physical input, MAP01, or efficiency.

| Gate | Required evidence / next boundary |
|---|---|
| Input authority and release | Fresh target/observation binding, no late new presses, independently verified release and finite recovery under stated faults. Blocking X11 I/O still prevents a universal release-time guarantee. |
| Local continuation and effect | Actual supported caller selects from fresh observations, checks independent application effect, and yields on unknown/stale state. |
| Continuous control / MAP01 | Measured input/release/environment timing, useful response and bounded recovery, with an independently checked task objective. |
| Integrated efficiency | Matched tasks/model/settings and baseline; correctness, all attempts, token/model accounting, latency, resources and failures. |
| Platform transfer | Qualify each supported platform/domain separately; do not transfer a Linux candidate result to Windows or another caller. |

The live parent Issues [#57](https://github.com/Unjuno/agent-interface/issues/57)
(integrated efficiency), [#59](https://github.com/Unjuno/agent-interface/issues/59)
(real-time control), and [#2789](https://github.com/Unjuno/agent-interface/issues/2789)
(usable desktop integration) were rechecked OPEN on 2026-10-19. Their update
timestamps differ; read the latest scope and ownership before shared changes
rather than treating this status check as a fresh assignment.

## Execution and preservation

- Follow the active user's scope and FINAL v5. Ordinary reversible investigation,
  implementation, local tests and authorized integration should proceed autonomously.
- Use the smallest discriminating experiment or repair. Do not repeat a consumed
  formal allocation; preserve first outcomes, raw, frozen conditions and limits.
- Check only resources and ownership needed by the selected operation. A dated
  inventory, open Issue or idle machine is not a resource grant. Closed historical
  logs are context; closing them does not prove release or impose a new global gate.
- Run relevant local validation; do not make optional remote CI a universal wait.
  Obey actual repository permissions/protection. This page adds no reviewer quota.
- Leave executed evidence, resulting decision and a concrete next action. Keep
  ideas open or carry their distinct unresolved work into an actual successor.

## Navigation and history

[Integration gates](INTEGRATION_PLAN.md) · [repository consolidation](REPOSITORY_CONSOLIDATION.md) ·
[ideas and outcomes](IDEAS_AND_OUTCOMES.md) · [research map](RESEARCH_MAP.md) ·
[current interface](../runtime/USING_CURRENT_INTERFACE.md) · [evidence map](EVIDENCE_MAP.md).

The previous 2,219-line document is preserved verbatim in
[CURRENT_GOAL_HISTORY_20261015.md](CURRENT_GOAL_HISTORY_20261015.md).
Its dated directions and allocations are history, not fresh instructions.
## Release-state diagnostic checkpoint (2026-10-23)

R04's input-free Win32 R02 diagnostic recorded the exact owned fixture in foreground on the active `Default` input desktop, successful input-desktop open with hook-control/read-object access, same named desktop for probe and fixture threads, and matching process integrity RID 8192. Neutral Ctrl/S/left-button `GetAsyncKeyState` samples were raw zero. The 10/10 auditor outcome is diagnostic completeness only; no input or release was tested. These conditions justify evaluating a narrowly scoped availability witness for interpreting zero as UP. The older public R03 receipt remains `release_unverified`; do not rewrite it. The implementation keeps UNKNOWN whenever foreground, active desktop, desktop access, or integrity cannot be proved. The separate R06 public trial passed for one owned fixture; it still does not establish bounded release under blocked I/O.

**R05/R06 public Win32 release qualification (2026-10-23):** R05 remains `FAIL_OR_UNKNOWN` under its frozen 11/12 auditor because the probe searched the wrong result nesting; its raw public report records completed and verified release, but this does not rewrite its outcome. A separate one-shot R06 with corrected pre-frozen extraction/audit passed 14/14: public stdio observe/validate/dispatch, exact fixture effect and event counts, verified release with empty down/unknown sets and active-desktop query witnesses, and clean fixture exit. See the R05 and R06 packets; this is one scoped fixture result and does not establish blocked-I/O timing, generation admission, recovery, MAP01, or efficiency.

**Blocked Win32 callback continuation (2026-10-24):** R14 observed a 650 ms
held callback with cancel pending and no release receipt; R15 stopped before
dispatch because the tracked goal document was dirty. R16–R19 are separate
one-shot public MCP attempts against owned fixtures, all on this PC; none used
WSLc or Docker. R16's effect check read the stale R14 sentinel. R17 and R18
matched their exact fixture effects, while all held-window polls remained
running/pending with release unconfirmed. R18's exact producer PID/creation-time
samples changed from indeterminate at +3.1 ms to exited at +251 ms, before the
2.0 s callback hold ended; the recovery-helper blockage explanation remains an
inference because helper stage was not directly traced.

R19 held the callback for 4.059 s. Cancellation changed to `unknown` at +2.866
s with release and replay both false and task success null, while action stayed
`running` in all 65 held-window polls. The producer identity was exited by +232
ms. The R19 sentinel effect was independently saved, and fixture/hook/foreground
cleanup succeeded; public close remained busy/UNKNOWN after 37 attempts. Its
frozen audit is `FAIL_OR_UNKNOWN` (6/9): two checks fail to read the callback
return and suppression evidence from the recorded event row; a third exposes
the unresolved action state by requiring action `unknown` alongside cancellation
`unknown`. The packet preserves that audit and raw; its result note separates
the audit extraction defects from the actual unresolved terminal-action and
input-release questions. These results narrow the boundary:
cancellation uncertainty becomes visible within 3.5 s even while the callback
is held, but action completion, release, recovery, and public close remain
unproved. The source path and existing focused tests confirm cancel and action
receipts are separate, and custody stays open while the owner is unresolved.
Do not repeat these one-shot trials. No verified unused WSLc allocation is
available, so this does not qualify WSLc or MAP01.

**Terminal action receipt follow-up (2026-10-24):** the R19 state path confirms
the supervised Win32 dispatch worker has itself returned when it observes
terminal cancellation `unknown`. At that boundary `mcp_server` now retains an
action result with `status=unknown`, `effect_status=unknown`, unknown
`input_dispatched`, `release_confirmed=false`, `task_success=null`, and
replay denied. It does not mutate owner custody; `interface_close` stays busy
while the owner phase is unknown. A composed MCP regression first failed on the
old `action=running` result, then passed after the change while asserting that
the owner remains unresolved. The four focused session, supervised-MCP,
operation-owner, and MCP server suites pass 69/69 in CPython 3.11.9 and 3.13,
both normal and optimized. Later full CLI verification exposed an offline
Fake X request-order mismatch: the standard caller emits a matching XTEST
KeyRelease between KeyPress and GetPointerControl, while the test-only parser
candidate discarded the association. R01 fixes that ordering, corrects the
lifecycle race to accept both scheduler-valid outcomes, and makes the
supervised cancellation test wait for its finalized receipt and bounded close
drain. The full CLI suite then passed 593 tests (8 skipped) in 149.996 s; the
focused parser, relay, composition, supervised-Win32 and lifecycle set passed
48/48 in normal and optimized CPython 3.11.9. Raw output, conditions and
limitations are in the [R01 packet](../research/integration/offline_proxy_reply_framing_20261019/standard-caller-order-r01/README.md).
These are local synthetic checks only. The public-caller Win32 path has not
been live-retested; a new run still requires a verified unused WSLc allocation
under the active goal. The newest [#7924 readiness update](https://github.com/Unjuno/agent-interface/issues/7924#issuecomment-6370065073)
records `WSLC_E_IMAGE_NOT_FOUND` before application code ran and no full
container-ID cleanup receipt; it retains STOP/HOLD and must not be retried as
the same allocation. A separate #9451 change repairs WSL version-log decoding,
not that image or ownership condition.

**Standard Win32 caller R20 terminal-action follow-up (2026-10-24):** after PR #9463 merged, one fresh public stdio-MCP attempt on the authorized Windows PC observed the exact producer exit during the held callback and action plus cancellation `UNKNOWN` within 3.5 s. Release/replay stayed false, runtime task success stayed null, close stayed busy, the held Q-down was suppressed on callback return, and the exact fixture effect/cleanup passed. The frozen auditor is preserved as FAIL_OR_UNKNOWN 7/10 because three checks read callback/suppression data from the pre-release snapshot; the separate post-hoc event-row audit passes 3/3. This confirms only bounded fail-closed terminal UNKNOWN for one run. It does not prove input release, recovery, MAP01, efficiency, reliability, or WSLc. Raw and both audits are in the [R20 packet](../research/integration/win32_supervised_standard_caller_20261024_r20/RESULT.md). WSLc remains STOP/HOLD under #7924; no WSLc or Docker operation was run.

**R20 readback qualification (2026-10-24):** while the R20 injected Q-down was stopped inside the low-level hook, an independent child read the same target generation and returned `q_down=false` at +194.855 ms; the callback did not return until +4013.465 ms. The hook calls `CallNextHookEx` only after its bounded wait, so the event had not reached the fixture during that sample. An UP readback under this schedule cannot distinguish an undelivered down event from a release and must not satisfy the release gate. The additive [R20 post-hoc audit](../research/integration/win32_supervised_standard_caller_20261024_r20/audit_supplement.json) now checks this ambiguity alongside the raw event-row corrections; the original frozen 7/10 audit remains unchanged. Next release evidence must include a witness that the down event crossed the held boundary and a distinct, independently observed up/recovery event. No WSLc or Docker run occurred.

**R21 bounded standard-caller recovery (2026-10-24):** one new Windows-PC public stdio-MCP trial held the injected Q-down callback for 249.367 ms after cancel, then forwarded it. Cancel returned pending in 1.3704 ms; the exact producer exited after callback return; public cancellation reached `recovered / release_confirmed=true` in 316.4537 ms; a later independent same-generation reader observed Q-up; the exact pre-cancel fixture effect and cleanup passed. The frozen audit remains FAIL_OR_UNKNOWN 8/10 because two checks read callback return from an intermediate snapshot taken before that timestamp was written. The additive [R21 supplement](../research/integration/win32_supervised_standard_caller_20261024_r21/audit_supplement.json) verifies final event rows and passes 7/7, but records PARTIAL: the retained public action still says `running`, and `interface_close` is `closed` with `release_confirmed=false`. The exact task effect precedes cancel; task success remains null. No WSLc or Docker operation occurred.

**Recovered terminal-action receipt repair:** when the cancellation receipt has recovered, the standard public dispatch worker now persists action status `recovered` only if the nested custody operation ID, target generation, phase, and release confirmation all match. It retains unknown effect and `input_dispatched`, null task success, and denied replay. The new public-MCP regression first failed on `action=running`; after the repair it passes with the existing UNKNOWN-custody and close-drain tests. The whole `runtime/cli_v1` suite passes 594 tests with 8 skipped in both normal and optimized Python. A fresh live attempt is still needed to verify this repaired terminal receipt on the PC. R21 is preserved; do not replay it. WSLc remains STOP/HOLD under #7924.


**R22 repaired-receipt retest (2026-10-24):** a new one-shot Windows-PC standard stdio-MCP attempt against source `e5e63a3` passed frozen preflight and source hashes. The callback forwarded the injected Q-down 259.200 ms after cancel returned; the exact producer exited 0.398 ms after callback return; Q-up reached the hook 5.407 ms after callback return; and an independent same-generation readback later observed Q-up. The retained public action and cancellation both reached `recovered` with matching generation and confirmed release. The repaired action preserves unknown effect/input-dispatched state, null task success, and denied replay. The exact fixture effect and owned cleanup passed, but the effect occurred before cancel. The original R22 audit remains FAIL_OR_UNKNOWN 8/10 due the same intermediate snapshot timestamp gap; the copied R21-specific supplement is unchanged and reports 6/7 because its old expected terminal-action gap is gone. New [R22 additive audit](../research/integration/win32_supervised_standard_caller_20261024_r22/audit_repair_followup.json) passes 9/9 evidence checks but classifies PARTIAL because `interface_close` says `closed` with `release_confirmed=false` while the cancellation and action receipts say true. Do not replay R22. No WSLc or Docker operation occurred; #7924 remains STOP/HOLD. Full local CLI suite had passed 594 tests and 8 skips in both normal and optimized Python before this packet-only report was added.


**R22 interpretation correction (2026-10-24):** the initial additive audit classified R22 PARTIAL because `interface_close` returned `closed / release_confirmed=false`. Review of the frozen condition and current `OwnedWin32SessionOwner.close()` shows that this flag is close-operation evidence and is intentionally false even when no calls remain; the frozen R22 PASS gate did not require it to be true. R22 therefore passes its narrow one-run cancellation/recovery criterion: confirmed public recovery, exact producer retirement, same-generation independent Q-up after callback return, fixture effect, and cleanup all passed without emergency Q-up. The frozen 8/10 audit and earlier 6/7 supplement are preserved; the post-hoc 9/9 audit remains archived with its over-strict PARTIAL label. Broader task success after recovery, MAP01, efficiency, and reliability remain unproven. See the [interpretation correction](win32-r22-result-interpretation-20261024.md).


**R23 same-generation continuation boundary (2026-10-24):** one new public stdio-MCP attempt on frozen source `dc78ace` reproduced confirmed cancellation recovery and same-generation Q-up: cancel pending in 1.5495 ms, exact producer exit 0.182 ms after callback return, Q-up at 4.499 ms after return, independent same-generation neutral readback, exact pre-cancel fixture effect and cleanup. A separately observed program with a new lease and new program ID, but the same target generation in the same session, was refused as `fresh target generation required after cancellation`; `operation_invoked=false` and `input_dispatched=false`, so no second input or effect occurred. The frozen auditor remains FAIL_OR_UNKNOWN 6/10 (one mis-nested action release assertion plus the rejected continuation hypothesis); additive [R23 audit](../research/integration/win32_supervised_standard_caller_20261024_r23/audit_followup.json) passes 10/10 for the recovery and fail-closed refusal, disposition `HYPOTHESIS_REJECTED_FAIL_CLOSED`. Current `OperationOwner` explicitly bars same-generation admission after recovery; the Win32 public session has no target rebind/review method. A new target generation/new-session attempt is still untested. R23 is preserved; do not replay it. WSLc remains STOP/HOLD under #7924.

R23's focused `runtime.guarded_win32_v1.test_operation_owner` suite passed 12/12 in normal and optimized Python, confirming the existing same-generation refusal invariant locally.

**WSLc local API runtime smoke S01–S04 (2026-10-24):** S01 found the pinned image absent in its inspected context and performed no pull or run. S02 and S03 both stopped before image/container operations because `wslc system session enter` did not create a new named session at the supplied path. S04 used the documented `Microsoft.WSL.Containers` 3.0.3 API instead: a unique session started, the pinned Python digest pulled once, and a single container configured with `NetworkingMode.None` and `ContainerVolume.ReadOnly=true` read the preregistered sentinel, rejected a write with `EROFS`, and exited 0. Its exact container and image were deleted and the session termination was recorded. The harness returned 1 due to a whitespace-sensitive JSON marker check; a separate raw-output audit confirmed the registered runtime assertions. The attempt remains `HOLD` because the storage VHDX (203,423,744 bytes, SHA-256 recorded in the packet) remained after session termination and the execution policy rejected deleting that exact generated file before the command ran. Packets: [S02](../research/integration/wslc_local_runtime_smoke_20261024_s02/README.md), [S03](../research/integration/wslc_local_runtime_smoke_20261024_s03/README.md), [S04](../research/integration/wslc_local_runtime_smoke_20261024_s04/README.md). This only qualifies WSLc API session/container execution and read-only mount behavior. It is not Win32 GUI, input-release, environment-response, recovery, task-effect, efficiency, or reliability evidence. The next computer-control gate remains a new standard-caller Win32 attempt with an independently witnessed Q-down, distinct Q-up/recovery, and independently audited task effect; no WSLc or Docker claim closes it.

**R34b standard-caller Win32 trial (2026-10-24):** one fresh attempt after a 10/10 input-free preflight recorded an independently confirmed same-generation Q-down before cancellation, 76 same-call status polls during a 1248.909 ms held callback, a recovery Q-up `SendInput` return at +624.284 ms, and an independent same-generation Q-up observation at +890.921 ms while the callback was still held. Public results later reached `recovered / release_confirmed=true`; exact producer exit followed the callback return. The separate hook trace still contained only one injected Q-up callback, with no second callback after release and none after exact producer exit. The supplemental audit is 20/22 FAIL_OR_UNKNOWN for those two hook-event gates; frozen audit execution retains its inherited `readback` NameError. The fixture click/save effect was independently observed before cancel, then a `q` character event appeared after save; runtime `task_success` remains null. Raw, preregistration, hashes and supplemental timing analysis are in [R34b](../research/integration/win32_supervised_standard_caller_20261024_r34b/RESULT.md). Do not replay this attempt. This is a bounded state-release/readback observation, not a strict hook-event PASS or post-recovery task-success claim.

**R34b hook-delivery qualification:** Microsoft’s [LowLevelKeyboardProc documentation](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc) says the hook runs on its installing thread, can be silently removed after callback timeout on Windows 7+, and has a 1000 ms maximum configured timeout on Windows 10 1709+. R34b’s measured callback lasted 1442.262 ms on build 26300; the timeout value was absent and the effective default was not measured. Silent hook removal is therefore a plausible explanation for the absent second event, not a proven cause and not a reason to change FAIL_OR_UNKNOWN. A sub-second follow-up can diagnose event visibility but cannot satisfy the frozen 1250 ms release gate.

**2026-10-25 real-provider composition smoke:** a current-main Codex App Server turn now joins the all-attempt recorder to the standard compiled public-MCP caller and independent Fake X pixel oracle ([series rollup](../research/integration/current_main_appserver_public_mcp_fake_x_20261025_ROLLUP.md)). p05 passed the synthetic provider/caller gate with reported 11,090 input, 410 output and 65 reasoning tokens; three preceding setup failures and one provider schema rejection remain retained. No model grounding, physical/live UI, WSLc, matched efficiency or broad reliability claim follows.
