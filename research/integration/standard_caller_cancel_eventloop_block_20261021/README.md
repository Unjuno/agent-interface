# Standard-caller cancellation event-loop stall probe

This local Fake X probe runs the current public MCP caller and measures whether unrelated coroutine heartbeats advance while `interface_guarded_cancel` waits in its synchronous owned-session cleanup path. It complements the construction-only process-start feasibility probe; it does not change production runtime behavior.

## Result

Run `r02` completed three trials per arm. With no injected cleanup delay, cancellation returned in 0–16 ms and the largest heartbeat gap was 16–31 ms. With a 700 ms synchronous delay at each of the XRes-disconnect and retired-input-release boundaries, cancellation returned in 1,406–1,407 ms and the largest heartbeat gap was also 1,406–1,407 ms. All six rows show `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`; the input call terminal is `runtime_failed` with the same conservative cleanup classification.

The observation is that the public async tool's current synchronous callback stalls the event loop for the duration of these cleanup waits. It supports separating caller responsiveness from cleanup work before integrating a bounded cancellation path. The arm delays are injected in the parent process; they are not actual `Process.start()` delays or live XRes/X11 calls. The release result itself is an injected UNKNOWN receipt. No physical release or product safety claim follows.

## Conditions and reproduction

Frozen inputs, scope and expectations are in `conditions.json`. Re-run with a fresh unique run ID so existing receipts remain immutable:

```powershell
python research/integration/standard_caller_cancel_eventloop_block_20261021/public-evidence/run_probe.py --run-id r03 --output research/integration/standard_caller_cancel_eventloop_block_20261021/public-evidence/raw/r03.json
python research/integration/standard_caller_cancel_eventloop_block_20261021/public-evidence/audit_raw.py
```

`public-evidence/raw/r02.json` contains all six trial records, exact timings and caller receipts. Per-trial request/report/close files and the initial observation are in `public-evidence/raw/trials/r02/`. `audit_raw.py` independently verifies trial counts, conditions hash, uncertainty/replay fields, terminal classification, latency separation and correspondence between cancel latency and heartbeat gap. `public-evidence/SHA256SUMS` covers the sanitized publication copy.

## Attempt history and limits

- `public-evidence/raw/setup-failure-01.stdout.txt` retains the initial launcher failure: running the script by path did not put repository root on `sys.path`, so runtime import failed before any caller operation.
- `public-evidence/raw/r01.stdout.txt` retains the next harness failure. It reached a standard-caller trial and preserved the copied request, report and 313-byte initial observation under `public-evidence/raw/attempt-01/`, but Windows refused to remove a temporary `.report.json.tmp` at context cleanup (`WinError 32`) before latency metadata was emitted. This attempt is incomplete and excluded from r02. No relevant Python child remained when checked.
- The driver now keeps each run under an immutable packet directory instead of deleting its output while the caller may still be writing receipts.

This used a Windows-host Python `spawn` owner process with the repository Fake X fixture. It used no X server, physical input, WSL/WSLc, Docker, or external model. The successful r02 result is descriptive method evidence only. It does not prove a hard bound, live release, blocked real platform I/O, target-generation correctness, task success, MAP01 behavior, matched efficiency, or reliability. WSLc Issue #7924 remains STOP/HOLD; this run does not grant or consume an allocation.

The proposed supervisor design remains pending written review under Issue #17; this probe only records the existing synchronous path and does not change runtime behavior.
## Shared evidence copy

The local `raw/` tree retains the original unredacted records and is intentionally excluded from publication. `public-evidence/` contains text-only redacted copies, the publication redaction record, and a separate `SHA256SUMS`. Only local checkout/user-profile/cache paths and the local host name were replaced; measured values, statuses, timings, request records, and synthetic images are unchanged. Run the public-copy auditor from `public-evidence/` where provided.
