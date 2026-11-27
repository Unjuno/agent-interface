# Queued-UP cancellation with and without X-server pause — R01

**Queued-UP observation/cleanup qualified in both cases; scientific task outcomes remain separate.** Two new frozen native WSL2/private authenticated Xvfb cases ran once each, no pause then one1000ms pause. Both public owned-process/prestarted-supervisor control tests ran exactly once/no skip, inner and host exit0. Each case's pre-frozen raw auditor reconstructs28 checks. Both retain old runtime UNKNOWN/null task-success/no replay and demonstrate a separate successful fresh task.

| Case | Cancel invocation→return | Old final count | Old task | Fresh task |
|---|---:|---:|---|---|
| No X-server pause | 95.170941 ms | 1 | PASS | PASS |
| X server paused1000ms | 254.854520 ms | 3 | FAIL | PASS |

This is one non-counterbalanced sample per condition. No general causal timing effect, speedup, model/token economics or reliability distribution is inferred. The declared300ms caller response, original composite/terminal bounds, independent all-up/horizon, distinct fresh target, strict task counts and owned cleanup checks pass. In the no-pause sample, cancel invocation→independent all-up was111.328756ms; in the paused sample, CONT receipt→independent all-up was103.609722ms. Those two intervals use different anchors and must not be compared as the same metric.

## Correction of earlier interpretation

Earlier PR #9426 descriptions, its two packets and related current-goal/Issue #57 notes called the old task an “explicit held-key” path. That API interpretation was incorrect: the old task is also `tail=[{'op':'key_chord','keys':['a']}]`. The injected factory flushes an8000ms delayed XTEST `b` press after `a` DOWN. In the repaired backend, `a` UP is queued after that delayed request, before entering real sync; it cannot overtake the earlier request. Thus the old repeated-handler result is a short chord stalled behind an earlier server request, not an intentional `key_state(..., True)` hold.

Historical raw, source, counts and outcomes remain unchanged. This additive correction supersedes the incorrect path descriptions in PR #9426/its integration notes and current-goal historical summaries. The matched completion-hold comparison in PR #9427 is unaffected: its hook runs after actual sync returns and has no earlier delayed XTEST request. Explicit-hold semantics in the backend really are unchanged by the repair, but that fact did not identify the old live test's operation.

## New evidence and conditions

The test factory now records `xvfb-target-release-queued.json` when the target KeyRelease Xlib call returns. The parent retains it and requires queue-return time ≤ recorded sync entry. This receipt explicitly says `server_release_confirmed=false`; it is not a server acknowledgement or an independent release readback. Both cases verify matching producer PID/client resource base/keycode and delayed-request flush ≤ target-UP queue return ≤ sync entry ≤ public cancel invocation. Separate X clients then read actual key states and non-idempotent task counts.

Source freeze: `708171052`; conditions freeze: `dac167ef8` before either case entry. Base main `d0d623ad2fe9e5dc7cc11aa184525a60055bf7d9`. [Comparison conditions](comparison-conditions.json), per-case conditions,219 source identities, all dependency versions, native preflight and complete host/inner exit receipts are retained. After the live run, a stale source comment was corrected; `postrun-comment-ast-check.json` confirms identical executable AST against the frozen source. The source manifest still binds the original run, not the edited comment. The only test-condition difference is the extra server pause; both use current repaired backend, the existing8000ms delayed request, acknowledgement hold0, process trace, prestarted supervisor, two inherited CPUs/nice+10 and8.5s horizon. The sync marker precedes the actual Xlib sync invocation; it is not a kernel syscall trace or proof about every possible transport stall.

`no-pause/` and `pause-1000/` retain full original public/native/owner reports, images, events, stdout/stderr, application count readbacks, target-UP receipt and source/process identities. Each raw auditor preserves the actual strict task result; the paused task FAIL is not relabelled PASS because control/recovery completed. Queue observability is an evidence endpoint, not task correctness. The producer-retirement/independent-supervisor recovery does not clear old UNKNOWN even in the one-effect case.

## Local verification, cleanup and remaining work

- `raw-red.txt`: actual injected factory/backend test first errors on the absent UP receipt. `raw-normal.txt` and `raw-optimized.txt`:28 related pure/signal-double/oracle/tap tests pass each mode after instrumentation; no native display is opened by those commands.
- The new regression exercises real factory and key methods over inert X requests, checking target-UP receipt before sync and no server-release claim.
- Both case audits are frozen before live entry, pass28 checks, and independently reconstruct data without importing the runtime scorer. No formal case was retried.
- Each owned Xvfb exited0. Separate per-case cleanup reads find owned server/test PIDs, old test-session members, lock and pathname socket absent, with no scan errors; final keys are up and fixture threads stop. Private auth cookies removed; warnings retained.
- Native WSL2 on the user-selected PC only. No WSLc/Docker allocation, shared runtime inventory, Windows desktop input, package install during the trial or model call.

The no-pause sample connects genuine earlier delayed-request cancellation to a counted one-effect task and fresh-task recovery. The paused sample preserves the counterexample: queuing UP and eventually releasing input cannot undo repeated task handlers. Remaining work includes stalled request writes, target/recovery authority, real application/MAP01 correctness, provider integration, matched efficiency and repeated reliability. No arbitrary exactly-once or hard release guarantee follows.
