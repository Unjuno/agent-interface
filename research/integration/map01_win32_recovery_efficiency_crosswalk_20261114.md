# MAP01 Win32 recovery and existing efficiency evidence crosswalk

This is an offline source/evidence audit. It does not combine unlike runs or
claim a Win32 recovery speedup.

| Requirement | Existing evidence | What it establishes | Remaining gap |
|---|---|---|---|
| Native input release after producer abnormal exit | R175–R181 local packets; current-main summary in `docs/CURRENT_GOAL.md` | Scoped single-run native recovery, late-input/neutral horizons, HUD 50→49 for R175 and reported R181 | No matched baseline; the R181 raw packet was not present in this checkout for independent file-level re-audit |
| Exception-recovery receipt through compiled caller | [PR #10293](https://github.com/Unjuno/agent-interface/pull/10293), merged as current main `1af9fef`; [retained R180 projection report](win32_compiled_obligations_r180_20261114/RESULT.md) | When the public action projection omits redundant `obligations`, the caller derives them from the exact retained program and requires equality with the cancellation receipt. Wrong obligations or stale generation fail closed. Source action stays UNKNOWN and task success is not promoted. Focused compiled caller passed 8/8 and public stdio MCP integration passed 32/32 in normal and optimized CPython on the candidate commit. Current main recheck passed the same focused 8/8 normal/-O and public stdio MCP 32/32 normal. | Raw R180 projection packet is not available in this checkout to repeat the before/after fixture adjudication; no fresh live GUI or recovery trial follows from the Fake X/stdio tests |
| Same-task direct vs compiled route timing | `docker_vizdoom_x11_caller_efficiency_20261028/RESULT.md` and 12 retained arm JSON files | Six counterbalanced direct/compiled pairs on Docker/Xvfb ViZDoom; all six pairs had verified release and effect; compiled was slower in all six | Does not measure abnormal producer exit, Win32, two-second recovery horizon, provider/model calls, or tokens |
| Repeated-grounding third arm | None in the inspected R14 packet; its arm directories contain only `direct` and `compiled` | No three-arm result can be claimed from this packet | Locate and independently audit the separate three-arm Calc evidence if relevant; do not merge its task timings with MAP01 |
| End-to-end model efficiency | P11/P12/P13 Fake X records elsewhere in the roadmap | Narrow public-caller task/usage accounting samples | Not MAP01 or native Win32 recovery; image-token/billing gaps and small samples remain |

The retained Docker/Xvfb comparison is a qualified **two-arm** comparison. PR
#10293 closes a compiled-caller projection gap but supplies no comparison arm.
A separate same-condition Win32 recovery comparison still needs a frozen
baseline arm and recovery arm with identical target, observation/task oracle,
model (or explicitly no-model protocol), input, deadline, process lifecycle,
and timer boundary. It must preserve failed attempts and score task effect and
release before comparing latency or tokens.

Recompute the retained raw summary from repository root with:

```powershell
python research/integration/audit_docker_vizdoom_efficiency.py
```

The audit requires the exact six pair IDs and both arms, all six gates per arm,
and no model/provider calls. It does not rerun the desktop experiment.

## R181 candidate custody recheck

The local R181 candidate folder contains the candidate code/fixture and frozen
conditions, but no R181 trial directory. The retained R180-only fixture audit
returns `verified: true` in normal and optimized CPython when the R181
conditions file is supplied through the runner's `R179_CONDITIONS` environment
variable. The candidate-specific 36-entry manifest matched on re-read. The
separate general manifest does not: its README and verification-summary entries
are stale relative to the current files, which were expanded after that manifest
was created. The README's bare audit command also fails because the runner
defaults to a missing `conditions-r180-final.json` in the candidate folder.
These checks support the retained R180 fixture only. No R181 live result/raw
packet is present here, so no native R181 conclusion is made from this audit.

The native host currently reports custody clear at revision 620, with no
pending obligation and no GZDoom process. Because the original R181 attempt
identifier and one-shot freeze must not be reused, any new native work needs a
new attempt ID, fresh frozen conditions, and a complete preflight. A higher
custody revision by itself does not identify which attempt produced it.


## R182 fresh native attempt (2026-11-14)

A distinct R182 attempt was frozen against current `origin/main` at
`1af9fef9e47f6a97433d50b8246ea3fcd12bc131`, custody revision 620, before
launch. The single MAP01 producer-exit trial completed with one accepted LEFT
down, producer-only exit 86, automatic recovery, no replay, and one returned
button-up call. The exception-to-supervisor receipt bound was 282 ms against a
750 ms limit. A separate two-second neutral horizon observed the same process
identity and generation with LEFT/W up. Source action remains UNKNOWN,
`release_confirmed=false`, and `task_success=null`; cancellation release is
separate and confirmed.

The pinned HUD oracle classified ammo 50 before and 49 after. The CUA receipts
independently show those same displayed values. The independent scene-change
measurement was only 0.0304%, below the preregistered 5% gate, so broad scene
response is explicitly NOT ESTABLISHED. Bounded normal close returned exit 0
without forced termination. The post-trial custody record was clear at revision
629; its `last_resolved.operation_id` and target generation match the R182
cancellation record.

Private raw evidence is under
`private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r182-fresh-native/trials/r182_native_win32_automatic_completion_recovery_map01/`.
The 112-entry manifest includes the frozen conditions and all trial files; all
size/SHA-256 checks passed. Manifest payload SHA-256:
`07c69fd57542b48cfbe1a59c30826432e8b74439c7d33e5ae1381ae69d6a1e5a`; raw
manifest-file SHA-256: `eee374c6ba0bd5093f73fcc6db60cacae1fdaa565d69965dd10bf9436d0a34ea`.
The 15 candidate offline tests pass normally and with optimized CPython. This
one scoped result does not establish reliability, efficiency, general task
effect, or close the missing same-condition comparison required by #57. R181
raw evidence remains unavailable in this checkout.


## Public caller composition follow-up

The current-main stdio MCP test
`test_stdio_exception_unknown_then_fresh_generation_recovery` passed in normal
and optimized CPython. It exercises the caller-visible exception result query
(`interface_results`), UNKNOWN/source custody preservation, and a distinct
fresh-generation recovery call through the public stdio surface. The test uses
a synthetic producer and recovery server; it validates API composition only,
not native GUI behavior.


## Expiry and late-operation boundary

The start-gate expiry test and the stdio MCP expiry/recovery/task-effect test
both pass on current main in normal and optimized CPython. Inspection of the
fixtures shows the stdio test's producer is held/synthetic and its action lower
bound is assigned directly; it does not attempt a real delayed post-expiry
input. The owner test proves a producer whose startup crosses expiry never gets
its gate opened and is reported not-dispatched only after exit/absence evidence.
R182's native two-second neutral horizon is a no-observed-input check after
recovery, not an injected delayed-operation challenge. A native delayed
post-expiry operation attempt remains unverified.


## Next native expiry discriminator

A new one-shot attempt should run one accepted LEFTDOWN, wait past a freshly
frozen lease deadline, then have a second LEFTDOWN in the still-running program.
Pass evidence must bind producer retirement, one native action only, separate
button-up recovery, exact neutral horizon, same process/generation, and HUD
50→49. HUD 48 or a second input proves the delayed operation crossed expiry;
unknown release/horizon or process mismatch also fails. Freeze a distinct attempt
and conditions only after a fresh clear-custody/host preflight. R182 remains
immutable and is not an allocation for replay.


## R184 native expiry result

R184 was a fresh, single native run against exact current main, with a 3 s
lease, first click, 8 s wait, then a scheduled second click. Expiry cancellation
retired the producer, returned a distinct LEFT button-up, passed the owner-bound
2 s horizon and an independent 2 s neutral horizon, and recorded release 31 ms
after the deadline. The same process/generation remained bound; postflight
custody was clear at revision 638; normal target close exited 0.

The frozen R184 gate is retained as failed. Its expected native count omitted
the `SetCursorPos` pointer move; the expected pre-expiry count for one click is
3 (move + DOWN + UP), matching the observed lower bound 3, so the delayed second
click input was not observed. Its cancellation-ID predicate also compared the
transaction ID rather than `action_operation_id`/nested source operation ID.
Independent after-capture HUD remained 50, so no expected task effect was
observed. Classify as partial expiry/release evidence with task effect
unestablished, not as an overall pass. The 176-entry private manifest has no
SHA-256/size mismatches; payload SHA-256
`9275b42d28c2b85ae779b4d896dc6156c9a282ce526b0915389293aa6828cbb8`.

The next unique attempt should retain the first LEFTDOWN through expiry (so
recovery performs the separate UP), then schedule a second DOWN after the wait.
Pre-register the counter as pointer move + first DOWN = 2; bind cancellation via
`action_operation_id`; require 50→49 and both neutral horizons.

**R186 native delayed-input expiry:** recovery/release/horizon boundary passed, but the preregistered one-shot effect did not. A held FIRE button remained down across the 3 s lease; the delayed balanced UP/second DOWN were not emitted (public action lower bound remained 2), yet the game repeated FIRE before lease expiry. Public image classification was `unknown`; CUA visibly read 50→44. This is evidence of pre-expiry repeat-fire semantics, not stale post-expiry input. It does not establish calibrated task correctness. Full local raw packet: 224 files, zero manifest mismatches, SHA-256 `74c59f1a6ba5ee03c1c2b84923113c637e0581e6ab947ce195d6fc147534d316`. Next: design a fresh attempt that has a meaningful recovery-release obligation without letting intended held-input repetition confound the exact effect oracle, then run and retain same-condition efficiency accounting. R186 is excluded from #57 efficiency comparison because it has no matched arms/model-token/provider accounting.


**R187 native delayed-input expiry:** The held-FIRE repeat confound from R186 was removed. A short first click plus SHIFT-only hold across expiry produced calibrated ammo 50→49. Cancellation returned separate LEFT button-up and SHIFT virtual-key-up receipts; owner and independent neutral horizons passed, expiry-to-release was 16 ms, and public action lower bound 4 excluded the scheduled SHIFT-UP/second click. Frozen scoped runner PASS, task_success null, one attempt only. Raw packet: 225 files, all hashes/sizes verified; manifest SHA-256 `ed72eb367f78cc37aa8e82d12f969f1de334d191655ec58bcdf2fadb7f8eaaa0`. This strengthens native expiry/release/effect evidence but does not establish reliability or #57 economics; the attempt lacks matched baseline/arms, model/provider tokens, and full resource accounting. Continue #57 with same-condition complete trials and retain the untested broader GUI/task boundaries.


**Retained Docker/Xvfb timing recomputation (2026-11-14):** `python research/integration/audit_docker_vizdoom_efficiency.py` re-read the retained 12 successful arms (six paired direct/compiled observations; pairs 1,2,5,6,9,10). Direct median was 877.792 ms, compiled median 926.063 ms, median paired difference +49.027 ms (+5.58%), with compiled slower in 6/6 pairs. The source report separately retains R11 and R13 failed pre-input harness packets; those are not timing arms. This remains a local descriptive one-action Linux/Xvfb result with no model/provider calls or token costs, and it does not compare native Win32 recovery or R187. Do not infer end-to-end efficiency from it.

**Attempt denominator and custody audit (2026-11-14):** The retained Docker/Xvfb source contains 20 recorded arm attempts across R10–R14: 12 passing measured arms (six matched pairs) and eight pre-input harness failures (pairs 3, 4, 7, 8; R11/R13). The metric recomputation uses the 12 extant passing `result.json` records. Custody is incomplete: the existing posttrial manifests expect 16 wrapper logs that are absent (R11: 4 Docker logs; R12: 4 Docker logs; R13: 4 stdout logs; R14: 4 stdout logs). Targeted filename search found no recoverable copies under the task's private-packets directory. The 8 R11/R13 attempts remain counted as failures from their matrices, but their wrapper logs are absent; the 12 successful arms retain result/bridge measurements but their wrapper logs are also absent. Thus the descriptive timing values reproduce from surviving records, while all-attempt packet custody is incomplete and is not a fully preserved 20-arm dataset. Do not regenerate historical logs or infer their contents. The audit script reports `PASS_METRICS_WITH_CUSTODY_GAPS`, 20 attempts, 12 passing, 8 pre-input failures, 16 missing manifest-listed logs, and `all_attempt_evidence_complete=false`. This still does not close #57's same-condition native Win32 recovery comparison or model/token/resource accounting.

## Current-main public caller ABBA result (2026-11-14)

The frozen R237/R238/R239/R240 ABBA packet compares direct public dispatch with
the public compiled caller under the same native MAP01 producer-exit recovery
condition. All four attempts passed the scoped release, late-input, neutral,
independent 50→49 HUD-effect and normal-close gates. The exact attempt ledger,
trial artifacts and manifest hashes are retained in the task-local packet
`private-packets/map01_native_windows_current_main_r217_exception_recovery_20261114/runner-candidates/r225-spawn-phase-profile/`;
see `REPORT.md` and `block-ledger.json` there. Direct interval median was
3.0800423 s (n=2) and compiled was 3.4401911 s (n=2), a descriptive 11.7%
compiled slowdown. The interval excludes common startup and manual visibility
gates; precise outer lifecycle timing is missing. Both routes made zero
provider/model calls, so token cost is not applicable. The result establishes
neither savings nor population reliability and remains a route-path comparison,
not an isolated recovery-policy comparison. Keep #57 open.

## #57 MAP01 expiry-trigger comparison seam — candidate implemented, native pair pending

The earlier automatic-recovery versus fresh-generation orphan-recovery proposal is not a matched expiry arm: `complete_exited_action` starts bounded automatic cancellation recovery when producer completion evidence is untrusted. Before this change, `_run_supervised_win32_dispatch` also invoked bounded cancellation at the authority deadline (2 ms maximum polling interval), so a caller `interface_cancel` at/after expiry raced with or followed it; before-expiry cancel changed the input-validity window.

The candidate branch now has an explicit research-only server setting, `--supervised-win32-deadline-cancel-policy public-caller`, with a fixed 1–2000 ms grace. Default `automatic` behavior is unchanged. In the public-caller mode, `interface_cancel` before the exact lease deadline returns `cancel_not_due` without setting cancellation state. At/after the deadline, the dispatcher waits for the caller's exact-call cancellation; if none arrives before `deadline + grace`, it invokes the same bounded monitor recovery. The result ledger retains policy, actual route (`public_interface_cancel` or `monitor_fallback_after_grace`), and caller-request monotonic timestamp when applicable. Calls after fallback begins are refused, and owner cancellation remains serialized so only one supervisor recovery is started. This creates a prospective pair that varies expiry-trigger routing while holding one program, lease deadline, admission, producer, target generation and recovery implementation constant. Completion-evidence failure before expiry still enters its separate automatic recovery path and is not an expiry-trigger comparison sample.

The public-MCP seam is now exercised both in-process and through a subprocess stdio MCP client/server, still with Fake Win32 ownership and a synthetic producer. The stdio case retains the request's absolute lease deadline, receives the exact pending call ID before expiry, sends one exact-call cancel after expiry, asserts the recorded request is within the planned 250 ms grace, and joins both the recovered/release receipt and exact-call effect verification to the same operation ID. Its fixture oracle reports failure, which remains `task_success=false`; no success is inferred. The focused MCP suite passes 40/40 normally and under `-O`. This is stronger public client/transport-shape evidence, not native behavior or a #57 efficiency result; provider/model calls are absent and token cost is not applicable.

The prospective four-pair protocol is recorded in [the expiry-caller pair draft](map01_win32_expiry_caller_pair_freeze_20261114.md). It fixes the candidate arms, caller deadline source, 250 ms grace, AB/BA sequence, denominator and separate route-interval/full-lifecycle endpoints. It is not an experiment freeze: exact action bytes, runtime/assets, calibrated oracle, live target, fresh allocation, and native custody remain missing. Both arms must still pass the same release, both horizons, no-late-input, calibrated HUD and normal-close gates. Keep the existing native ABBA route result separate; it uses zero provider calls and is not this recovery-trigger pair. Even a scoped infrastructure pair alone would not meet #57's broader integrated model/token-efficiency requirement. Until native paired evidence and complete accounting are retained, #57 remains open.

Any future paired allocation must use current source, pinned GZDoom/Freedoom assets, identical isolated MAP01 task state and oracle, unique IDs, clear pre/postflight custody, counterbalanced order, and complete all-attempt records. Capture common admission-to-verified-release/effect and full-lifecycle endpoints, monotonic event timestamps, CPU/working set, source/cancellation receipts, exact operation/generation bindings, both two-second horizons, calibrated ammo, bounded normal close, model/provider/token accounting and every failure. Require the preregistered correctness gates in both arms before comparing speed; otherwise report all attempts and no speed winner.

This proposal remains unresolved. The newly completed R196 single-arm repeat below advances native expiry/release/effect evidence but does not supply a matched #57 efficiency comparison.

## Current-main native delayed-input repeat R194–R196 (2026-11-14)

R194 and R195 are retained as pre-input runner/setup failures. R194 launched the exact pinned GZDoom process and showed MAP01/ammo 50 in Computer Use, but the runner packet omitted `server_with_expiry.py`; stdio initialization returned `Connection closed`. `action_started=false`, custody remained clear at revision 683, and no input was dispatched. R195 included the server entrypoint but stopped on `KeyError: r194_click_hold_ms` against the frozen `r195_click_hold_ms` condition. It also remained pre-dispatch with HUD 50, clear custody, and no replay. Both targets were closed through Computer Use; exit codes were not observed. Their 13- and 37-entry manifests have zero mismatches (manifest-file SHA-256 `9f80e481023811f7cb458322942ef21e490d56ef804c1850d117128c8263ab04` and `aad226087b3a50aade9f5f8bca72e379bf176ceee669e903c140f949636803e2`). Do not treat either as an effect/recovery trial.

R196 was frozen against exact current main `4e8c463a6d7f8dde2a9ec684cbf45280e9f760cf`, tree `c580f1064e6106ca7f5ae2d8be34bc53039d1e03`, with 11 current runtime hashes and clear custody revision 683. Read-only preflight passed. The native run dispatched once, accepted one LEFT click with a 120 ms DOWN dwell, then held SHIFT through the 3 s lease while the delayed SHIFT-UP and second click remained queued after an 8 s wait. The lower-bound count was four (pointer move, LEFT DOWN/UP, SHIFT DOWN), so neither delayed operation was emitted. Automatic bounded cancellation returned separate source action/cancellation release receipts; owner-bound and independent two-second neutral horizons passed; expiry-to-release receipt was 15 ms against a 1 s bound. The exact calibrated HUD effect was 50→49. Broad scene change was 304/1,003,200 pixels (0.0303%), below the 5% gate; `task_success=null`, replay denied. The owned GZDoom process closed with exit 0 and no forced termination; custody returned clear at revision 692.

R196 raw is local-only under `private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r193-current-main-held-click-repeat/trials/r196_native_expiry_delayed_second_click_map01/`. Its 239-entry manifest independently rechecked with zero size/hash mismatches; payload SHA-256 `51989fd268c64d56e59e77f098a6254ba810d59b27554a8b55c7b0a6ab5b69db`; manifest-file SHA-256 `e561219f943f16c5eb2d780f8601672477cd8d20b18825df8ff869caeb038cae`. Frozen conditions SHA-256 is `21bb769924410a1ad42de44e60ecd69881e469c0bc620e8bfcbb573ec92cf35e`. The trial packet contains hash-checked snapshots of the 36 source/oracle files named by the frozen conditions. This is one scoped repeat of the 120 ms dwell condition; together with R191/R192 it supports further replication, but does not prove causality or reliability. R196 is not an abnormal producer-exit trial and supplies no matched #57 efficiency arm.

R197 is a fresh repeat on the next exact main commit `7dcc86af50c3532b845964c8004d2cb4aaafc07e` (documentation-only delta from R196), with a unique attempt, program, lease and trial directory. It again emitted exactly four native inputs, blocked the scheduled post-expiry operations, separately confirmed release, passed the owner-bound and independent 2 s horizons, and returned the recovery-release receipt 15 ms after authority expiry. The calibrated HUD again showed 50→49; broad scene change was 324/1,003,200 pixels (0.0323%), below threshold, and `task_success` remains null. The owned process exited 0 without forced termination; custody is clear at revision 701. R197 raw is local-only beside R196. Its 262-entry manifest independently rechecked with zero mismatches; payload SHA-256 `ce9372f8f494943932da4405fef01dbdec16c3ab3b534d1f8928c881ffb4baaf`; manifest-file SHA-256 `d3a38a7c503f4a9f35ddcae9232b0c9efa3d29b38c4c1c575bed6264c221263c`. Frozen conditions SHA-256 is `727ea4dc6c918930d2c4b61086910df5a322422f8f759f3015ec4e314a11d2cb`. The packet contains hash-checked snapshots of all 38 frozen runner/oracle files. R196/R197 are two same-runtime scoped repeats; they do not establish causality, general reliability, abnormal producer-exit recovery, or a matched #57 efficiency result.

**R188 follow-through:** The proposal was converted into one new, frozen single-arm repeat, not a matched efficiency pair. Atomic current-logon custody snapshot was clear at revision 656; pinned runtime hashes and assets matched; read-only runner preflight passed. The GZDoom window rendered MAP01/ammo 50, but a Docker Desktop WSL error modal prevented the exact foreground/root-foreground gate. The attempt timed out before input, remained `action_started=false`, and produced no effect/recovery/timing sample. A Computer Use Alt+F4 cleanup request was followed by later absence of the target process; no exit code was captured, so normal close remains unverified. Custody stayed clear with pending null. Raw packet has 10 files, all manifest checks pass; see [R188 trial record](map01_native_win32_recovery_r182_20261114.md#r188-native-map01-repeat-attempt-2026-11-14). Count it as a pre-input failure, never retry its ID. Docker's WSL error modal remains an environment gate; no restart completed in this attempt. #57's matched recovery arms, all-attempt economics, model/token/resource report and the 16 missing historical wrapper logs remain unresolved. The authored matched-policy design above is still not a formal run allocation.

**R188 Docker UI follow-up:** Computer Use confirmed the Docker Desktop WSL error dialog remains. It reported a Restart control, but both click attempts mapped to ChatGPT.exe/Chrome Legacy Window and were rejected; the screenshot content did not match the Docker accessibility tree. No restart or other Docker state change was performed. See the R188 raw environment record; the 11-file manifest is verified at SHA-256 `c860644f71b4296e0efe20f155a09d67daab4f060f05c7819c7a6fcc238ad85d`. This provider window-owner mismatch explains why the native pre-input gate cannot currently be satisfied through Computer Use, while R187's input-release/effect evidence remains intact.

**Docker daemon recovery follow-up (2026-11-14):** Rechecked the host after R188: `wsl.exe --version`, `--status`, and `--list --verbose` each exited 0; Ubuntu and `docker-desktop` were stopped, while `vmcompute` and HNS were running. Docker Desktop still showed `Docker Desktop is unable to start`. The Docker window’s screenshot/accessibility pairing was inconsistent after one restart click attempt, so the click was not repeated. Using the user-authorized Docker Desktop CLI instead, `docker desktop restart --detach` returned `Starting Docker Desktop`; subsequent `docker desktop status` was `running` and `docker info` returned Server 29.8.1 with 16 registered containers, 0 running. Computer Use no longer listed a Docker window after this restart, but the daemon was healthy. Exact local observation: `private-packets/docker_restart_followup_20261114.json`, SHA-256 `398c2fc4e304ba487fd474353a7a56769593bd563b9844b582cbccca6b5be6ce`. This clears the daemon-start blocker only; it does not provide a MAP01 trial, recover the missing historical wrapper logs, or complete #57's matched recovery/economics comparison. The 16 containers were left stopped.

**R189 native foreground handoff gate:** A fresh unique R189 condition set froze with clear custody revision 656; all 11 runtime hashes matched the R187 set; the offline gates passed 21/21 in normal and `-O`. Computer Use produced a screenshot of the exact GZDoom window with MAP01 HUD/ammo 50, and its window ID/PID matched the runner request. However, the runner's independent foreground check read the ChatGPT host HWND (`3080454`), so it rejected the receipt before dispatch (`action_started=false`). No recovery or task-effect measurement occurred. The GZDoom target later disappeared from Computer Use after a close-key attempt; its exit code is unavailable. Postflight custody matched the clear revision-656 preflight. Raw packet: 11 files, zero manifest mismatches/extras; manifest SHA-256 `383351047bd2a1e691bd703f5905a2efc261e1e7e21b40a2989705fbf045be9c`; frozen condition SHA-256 `45ab91b31c207171ab24b6c4c051588bf443136ab3c95d3215f92cef2233616f`. A separate read-only focus probe then found that `sky.activate_window` by itself left the exact GZDoom HWND/PID in the foreground; the prior combined activate-plus-screenshot call had not. Next unique trial should capture the passive screenshot first, activate in a separate final Computer Use call with no subsequent capture, then hand the receipt to the runner. R189 remains a pre-input failure and must not be replayed.

**R190 native effect repeat:** The split activation protocol passed the independent exact-window foreground check. A single R190 native dispatch emitted a lower bound of four actions (cursor move, LEFT DOWN/UP, SHIFT DOWN), then bounded expiry recovery retired the producer, separately released LEFT and SHIFT, excluded the post-wait SHIFT-UP/second click, and passed both two-second horizons. Release receipt arrived 16 ms after expiry; GZDoom closed normally (exit 0); custody returned clear at revision 665. However the exact pre-registered effect failed: the calibrated HUD read 50 before and 50 after, and the independent scene-change fraction was 0.0315%, so the attempt is `FAIL_SCOPED_EXPIRY_DELAYED_OPERATION_BLOCKED`, not a task-effect pass. This confirms OS-level `SendInput` accounting and release do not prove application consumption. R187 used the same immediate LEFT DOWN then UP sequence and produced 50→49; R190 did not, so the effect is not yet repeatable. Backend inspection confirms there is no wait between those two SendInput calls. The next unique attempt should insert a preregistered 120 ms `wait_update` between the initial LEFT DOWN and UP, retaining the same delayed post-expiry sequence and four-event input lower bound; this tests whether a zero-dwell click edge is intermittently missed without extending the held FIRE period. Raw packet has 223 files with zero manifest mismatches/extras; manifest SHA-256 `1c4f0929c31aabdcd5a33ac525527c36bc16f93b1382a3bdfba5743c805e6eb9`; frozen condition SHA-256 `099e1a30eb1e2247c874a4b8b510087dcbb725b341025d930b9871bf25d286fb`. Keep R190 in the all-attempt denominator and do not replay it.

**R191 native held-click dwell follow-up:** R191 froze a unique new attempt after custody revision 665 was clear. It retained the R187 3 s lease, SHIFT-only hold across the 8 s wait, delayed post-expiry SHIFT-UP/second click, and four-event pre-expiry lower bound, while inserting a 120 ms `wait_update` between LEFT DOWN and UP. Normal and optimized offline gates passed 21/21 each. The split Computer Use sequence (passive target screenshot, separate activation-only call, receipt) passed the independent foreground/HWND/PID check before input and after recovery. One dispatch returned source/cancellation `recovered`; lower bound 4 excluded both delayed operations. Separate LEFT/SHIFT releases were confirmed, owner-bound late-input horizon and independent neutral horizon passed, and expiry-to-release receipt was 16 ms. The calibrated HUD classified 50→49, matching the Computer Use post-recovery screenshot; thus the scoped task-effect gate passed. The broad scene-change detector remained below its 5% threshold (0.0307%), so no scene-motion effect is claimed. GZDoom exited normally with code 0 and no forced termination; postflight custody is clear at revision 674, pending null. `task_success` remains null and replay is denied. Raw packet: 221 files, zero manifest mismatches/extras; manifest SHA-256 `42d666473557b1c03126cb4e65ad350e55859fc9e49f5b490fb524d453505972`; frozen condition SHA-256 `e3014558bac523d62a6ea2d53b8246783457f830957898c90a5f0b9075f529a2`. This is a meaningful scoped repeat after R190's 50→50 result, but one R191 pass does not prove that the 120 ms dwell caused the difference or establish reliability. Repeat the frozen effect under new IDs before generalizing. R191 does not provide the matched recovery-policy efficiency arms or close #57.

**R192 held-click dwell repeat:** A distinct R192 attempt reused the frozen 120 ms LEFT DOWN dwell with a new ID and fresh preflight (clear custody revision 674); offline gates again passed 21/21 normal and `-O`. The exact-window split activation gate passed at both stages. R192 reproduced HUD 50→49, four-event lower bound, exclusion of delayed SHIFT-UP/second click, separate LEFT/SHIFT recovery release, verified owner and independent two-second horizons, and expiry-to-release receipt 16 ms. GZDoom exited normally (0); postflight custody is clear at revision 683. The independent broad scene-change metric stayed under threshold (0.0320%). Raw packet: 223 files, zero manifest mismatches/extras; manifest SHA-256 `f48e1b2efeccfecbcd08763f4ab89a9efb409b08b4d00d354c1b98c7af5961af`; frozen condition SHA-256 `5b32b8249aa90b8eecfc4205cda5c1f64a109065259b4befd44534d23c4b2d63`. Across the available independent attempts, immediate DOWN/UP produced one 50→49 (R187) and one 50→50 (R190); 120 ms dwell produced 50→49 in R191 and R192. This small sequence supports further testing of the dwell hypothesis, not a causal or reliability claim. `task_success` remains null, and #57's matched recovery-policy efficiency comparison remains unrun.
