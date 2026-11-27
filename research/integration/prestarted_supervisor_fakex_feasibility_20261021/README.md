# Prestarted supervisor Fake X feasibility probe

This packet tests one narrow construction question: can a caller with an already-ready supervisor return `UNKNOWN` near a fixed cancellation deadline while a delayed worker launch finishes later, with late and stale-generation effects rejected by an independent state oracle?

## Frozen conditions and execution

`conditions.json` is the frozen trial definition. The run used Windows-host Python 3.11 with multiprocessing `spawn`, a loopback JSON Fake X state server, 3 trials per arm, and `time.monotonic_ns` timestamps. It used no WSL/WSLc, Docker, X server, Xlib, physical input, or external model.

The complete twelve-trial receipts are in `public-evidence/raw/r01.json`. Its embedded audit reports `PASS` with no failures. `conditions_sha256` binds that result to the condition file. `public-evidence/SHA256SUMS` records the sanitized-copy hashes. The captured r01 is immutable; verify it with `python research/integration/prestarted_supervisor_fakex_feasibility_20261021/public-evidence/audit_raw.py`. Any new construction trial must use a new output path and run identity, leaving r01 intact.

## Result

| Arm | Trials | Caller response | Fake X state/effect |
|---|---:|---:|---|
| Synchronous delayed start | 3 | 812–844 ms; all exceeded the 300 ms deadline | All late KeyRelease attempts rejected as expired; key remained down |
| Prestarted supervisor, delayed worker start | 3 | 296–313 ms; `UNKNOWN` at the deadline, within the 150 ms response slack | All late KeyRelease attempts rejected as expired; key remained down; supervisor receipts arrived after the deadline and workers retired |
| Prestarted supervisor, fast control | 3 | 140–157 ms; completed before the 2000 ms deadline | Exactly one KeyRelease accepted per trial; independent readback showed key up |
| Prestarted supervisor, stale generation | 3 | 140–141 ms; completed before the 2000 ms deadline | All stale KeyRelease attempts rejected; independent readback showed key still down |

The experiment supports a construction-level claim that moving process creation behind a ready supervisor can avoid charging injected worker-start delay to the caller's response path, while the caller reports uncertainty and the Fake X oracle refuses expired or stale effects. It does not qualify production supervisor code or a real GUI path.

## Limits and next discriminator

Fake X is a purpose-built loopback JSON oracle, not the X11 protocol. Its acceptance timestamp and independent state readback are not physical input evidence. The probe does not exercise blocked platform I/O, the standard caller, observation/effect timing, bounded recovery, task success, MAP01, reliability, or matched efficiency. The next useful discriminator is to implement the same absolute-deadline and generation fencing in the existing runtime seam, then drive it through the standard caller against a real X server with independent input readback. That integration work remains separate from this passing feasibility result.

The first invocation exposed a Windows `spawn` pickling error because the probe replaced `Process.start` with a local closure. The driver was corrected to inject the same delay in the parent immediately before calling `start()`. Only the successful corrected run is retained as `r01`; the failed attempt made no successful trial packet and did not modify runtime code.
## Shared evidence copy

The local `raw/` tree retains the original unredacted records and is intentionally excluded from publication. `public-evidence/` contains text-only redacted copies, the publication redaction record, and a separate `SHA256SUMS`. Only local checkout/user-profile/cache paths and the local host name were replaced; measured values, statuses, timings, request records, and synthetic images are unchanged. Run the public-copy auditor from `public-evidence/` where provided.
