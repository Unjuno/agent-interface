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

## Next #57 MAP01 matched recovery comparison — freeze proposal, not an allocation

The next informative comparison should isolate recovery policy after the same already-accepted GUI input. Use two arms on the same Windows host, exact current source, pinned GZDoom/Freedoom binaries and identical isolated per-arm MAP01 state:

- **Auto arm:** one short LEFT tap (expected ammo 50→49), then SHIFT down; force the same producer-only abnormal exit at the frozen point after the action lease expires. Let the supervised caller perform its normal bounded completion recovery.
- **Explicit-recovery baseline:** issue the identical tap/SHIFT program and inject the same producer exit at the same lease boundary, but use the public caller's separate `interface_recover_orphaned_input` flow from a fresh server/generation after preserving UNKNOWN source custody. This is the strongest available simple recovery baseline, not a no-recovery strawman.

Use at least six counterbalanced matched pairs (AB/BA order balanced), with one freshly initialized target/process per arm. Keep model/provider calls at zero in both arms; this isolates caller/recovery cost and makes token cost exactly zero by protocol. Record any setup/model work separately and include both (a) the same admission-to-verified-release/effect endpoint and (b) full lifecycle including startup, source preservation, fresh-generation observation, recovery, scoring, normal close and custody postflight. Capture per-arm monotonic timestamps, CPU time, peak process working set, exact input/release receipts, producer exit, source UNKNOWN status, separate recovery receipt, generation and operation bindings, 2 s owner and independent neutral/late-input horizons, calibrated before/after ammo, and all cleanup exits. Keep the timing and resource measurements for failed arms too.

A pair is correctness-eligible only if both arms show exactly one ammo decrement (50→49), correct source/recovery operation and process/generation bindings, distinct release evidence, all horizon gates, replay denied for the UNKNOWN source, and normal bounded close. Any failure stays in the denominator and fails that arm; never replace it. Report medians and per-pair deltas for both timing endpoints, peak working set/CPU, all-arm failure counts, and zero provider/token use. Do not claim a speed win unless all frozen correctness gates pass and paired outcome uncertainty is reported. This scope compares two recovery policies for this one MAP01 task; it does not establish general reliability or all computer-control performance.

This was a proposal only; the updated current snapshot and the resulting failed attempt are recorded below.

**R188 follow-through:** The proposal was converted into one new, frozen single-arm repeat, not a matched efficiency pair. Atomic current-logon custody snapshot was clear at revision 656; pinned runtime hashes and assets matched; read-only runner preflight passed. The GZDoom window rendered MAP01/ammo 50, but a Docker Desktop WSL error modal prevented the exact foreground/root-foreground gate. The attempt timed out before input, remained `action_started=false`, and produced no effect/recovery/timing sample. A Computer Use Alt+F4 cleanup request was followed by later absence of the target process; no exit code was captured, so normal close remains unverified. Custody stayed clear with pending null. Raw packet has 10 files, all manifest checks pass; see [R188 trial record](map01_native_win32_recovery_r182_20261114.md#r188-native-map01-repeat-attempt-2026-11-14). Count it as a pre-input failure, never retry its ID. Docker's WSL error modal remains an environment gate; no restart completed in this attempt. #57's matched recovery arms, all-attempt economics, model/token/resource report and the 16 missing historical wrapper logs remain unresolved. The authored matched-policy design above is still not a formal run allocation.

**R188 Docker UI follow-up:** Computer Use confirmed the Docker Desktop WSL error dialog remains. It reported a Restart control, but both click attempts mapped to ChatGPT.exe/Chrome Legacy Window and were rejected; the screenshot content did not match the Docker accessibility tree. No restart or other Docker state change was performed. See the R188 raw environment record; the 11-file manifest is verified at SHA-256 `c860644f71b4296e0efe20f155a09d67daab4f060f05c7819c7a6fcc238ad85d`. This provider window-owner mismatch explains why the native pre-input gate cannot currently be satisfied through Computer Use, while R187's input-release/effect evidence remains intact.

**Docker daemon recovery follow-up (2026-11-14):** Rechecked the host after R188: `wsl.exe --version`, `--status`, and `--list --verbose` each exited 0; Ubuntu and `docker-desktop` were stopped, while `vmcompute` and HNS were running. Docker Desktop still showed `Docker Desktop is unable to start`. The Docker window’s screenshot/accessibility pairing was inconsistent after one restart click attempt, so the click was not repeated. Using the user-authorized Docker Desktop CLI instead, `docker desktop restart --detach` returned `Starting Docker Desktop`; subsequent `docker desktop status` was `running` and `docker info` returned Server 29.8.1 with 16 registered containers, 0 running. Computer Use no longer listed a Docker window after this restart, but the daemon was healthy. Exact local observation: `private-packets/docker_restart_followup_20261114.json`, SHA-256 `398c2fc4e304ba487fd474353a7a56769593bd563b9844b582cbccca6b5be6ce`. This clears the daemon-start blocker only; it does not provide a MAP01 trial, recover the missing historical wrapper logs, or complete #57's matched recovery/economics comparison. The 16 containers were left stopped.

**R189 native foreground handoff gate:** A fresh unique R189 condition set froze with clear custody revision 656; all 11 runtime hashes matched the R187 set; the offline gates passed 21/21 in normal and `-O`. Computer Use produced a screenshot of the exact GZDoom window with MAP01 HUD/ammo 50, and its window ID/PID matched the runner request. However, the runner's independent foreground check read the ChatGPT host HWND (`3080454`), so it rejected the receipt before dispatch (`action_started=false`). No recovery or task-effect measurement occurred. The GZDoom target later disappeared from Computer Use after a close-key attempt; its exit code is unavailable. Postflight custody matched the clear revision-656 preflight. Raw packet: 11 files, zero manifest mismatches/extras; manifest SHA-256 `383351047bd2a1e691bd703f5905a2efc261e1e7e21b40a2989705fbf045be9c`; frozen condition SHA-256 `45ab91b31c207171ab24b6c4c051588bf443136ab3c95d3215f92cef2233616f`. A separate read-only focus probe then found that `sky.activate_window` by itself left the exact GZDoom HWND/PID in the foreground; the prior combined activate-plus-screenshot call had not. Next unique trial should capture the passive screenshot first, activate in a separate final Computer Use call with no subsequent capture, then hand the receipt to the runner. R189 remains a pre-input failure and must not be replayed.
