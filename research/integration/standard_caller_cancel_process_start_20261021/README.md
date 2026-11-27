# Standard-caller process-start cancellation probe

## Result

Run `r02` completed six trials through the public standard MCP caller on Windows using Python 3.11 `multiprocessing` spawn and the repository Fake X owned-session fixture. Each trial started exactly one real helper. The synthetic disconnect receipt did not arrive within the current 150 ms XRes supervision budget, so the worker was retired and the caller preserved `owner_client_disconnect=unknown/supervision_timeout`; release remained `not_attempted` in every trial.

No-delay cancellation and maximum heartbeat gap were 172 ms in all three trials. With a 700 ms delay injected immediately before the actual `Process.start()` call, both measurements were 875, 891, and 890 ms. This demonstrates that process-start delay is synchronously included in the public cancel response and pauses the MCP event loop. It does not establish an OS hard bound, successful input release, live XRes behavior, or task success.

All six terminal records retain `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`. The scoped independent auditor passes the frozen conditional expectation in `conditions-r02.json`; PASS is about evidence completeness and expected gate behavior only, not product safety.

## Reproduction and retained evidence

Run a fresh immutable ID; do not overwrite `r01` or `r02`:

```powershell
python research/integration/standard_caller_cancel_process_start_20261021/public-evidence/run_probe_r02.py --run-id r03 --output research/integration/standard_caller_cancel_process_start_20261021/public-evidence/raw/r03.json
python research/integration/standard_caller_cancel_process_start_20261021/public-evidence/audit_raw_r02.py
```

`public-evidence/raw/r01.json` remains a preserved FAIL: its original condition expected two helper starts, while all six actual trials reached only one because the disconnect gate stopped before release. Its source and conditions snapshots are stored alongside it. `public-evidence/raw/r02.json` applies the corrected conditional expectation without changing r01. Each run's request, terminal, helper, and close records remain under `public-evidence/raw/trials/<run-id>/`.

The exact conditions and source revision are recorded in `conditions-r02.json`. `public-evidence/SHA256SUMS` covers the sanitized publication copy. `audit_raw_r02.py` independently checks hashes, trial completeness, helper custody, UNKNOWN/no-release fields, and arm separation.

## Scope

This was a local Windows/Fake X construction probe. It used no X server, physical input, WSL, WSLc, Docker, or external model. The actual child-process creation and standard-caller cancellation path ran; the child worker's XRes result and the possible release result were synthetic. The result supports prioritizing a nonblocking, prestarted cleanup supervisor design. It does not validate that design, prove a release path, or resolve MAP01/live control. No WSLc allocation was used or inferred.
## Shared evidence copy

The local `raw/` tree retains the original unredacted records and is intentionally excluded from publication. `public-evidence/` contains text-only redacted copies, the publication redaction record, and a separate `SHA256SUMS`. Only local checkout/user-profile/cache paths and the local host name were replaced; measured values, statuses, timings, request records, and synthetic images are unchanged. Run the public-copy auditor from `public-evidence/` where provided.
