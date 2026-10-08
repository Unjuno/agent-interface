# Formal result — Issue #3711 downstream truncation, allocation 02

## Disposition

`PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY` — one frozen synthetic allocation, independently audited in a separate fresh Docker container. This is not a live task or runtime-wide reliability result.

## Execution

- Base source: main `2dff80852292cc82fd5c23a449c8244bea94bc25`.
- Engine: OrbStack Docker 29.4.0, `linux/arm64`; Python 3.12.14.
- Image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Container: `--network none`, read-only root and source mount, bounded `/tmp`, isolated writable result directory; no live model, GUI, display, or native input.
- Frozen import closure, runner, and auditor matched `successor-02/FREEZE.json`.
- The producer call used a deterministic synthetic backend. No real dispatch backend was invoked.

## Observations

The actual CLI `main()` presentation path made one stdout write. The sink reported acceptance of all **246 characters** but delivered only the first **23 bytes**. Parsing the received prefix raised `JSONDecodeError` (`Unterminated string starting at: line 1 column 20 (char 19)`). The CLI returned exit code **0** because the writer reported a full accepted write; that is recorded as an important residual boundary, not hidden by the parser rejection.

The actual read-only `attempt-status` command then returned `report_recorded`, `replay_allowed=false`, exit code 0. The synthetic dispatch count remained 1. The request and report bytes/hashes and complete attempt-directory snapshot were identical before and after recovery:

- request SHA-256: `92bacf5e4a7550bc6ef3d605c0dbb7662cbac29eb12076e07c650f10ff915f57` (381 bytes)
- report SHA-256: `516a2a999b7a0591d78b73a8e2e41b800d434d3077ed08a57cdf4b39fcc4b584` (140 bytes)
- accepted write SHA-256: `e8ef9f6dd897325a22b1927d27e7fba2948051bb309cc472bbf2a1bfaba863d1`
- delivered-prefix SHA-256: `0450145d98f8ff197766d91827a438db1aa5800d556b4bee24eb57b33e168d4a`

The separate-container auditor returned PASS with zero errors. Its raw evidence digest is `3f51dc5a4c9c8acb48fc2929a8219260575271e5794cd5bd4afedf6f712afc73`; the machine-readable audit is `audit.json`.

## Interpretation and limits

This experiment establishes that a generic JSON parser rejects this intentionally truncated prefix and that retained report recovery is read-only and does not replay the synthetic dispatch. It does **not** establish that every CLI caller parses stdout rather than trusting exit status. In this probe the producer returned exit code 0 after downstream truncation because its writer reported the entire write accepted; a caller relying only on that exit code could still misclassify delivery. This integration-level consumer/exit-status behavior remains for independent review.

The truncation was injected by a bounded in-process sink, not an OS pipe or network proxy. There was no power-loss test, real API/backend call, GUI action, task effect, performance measurement, or production claim. Allocation 01's source-mount STOP and the earlier import-only construction checks remain separately preserved and unchanged.
