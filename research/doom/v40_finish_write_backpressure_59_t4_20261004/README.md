# V40 finish-pipe backpressure repair (T4, 2026-10-04)

## H / T / D / C / U

**H:** `ControllerSessionCustody.finish()` must return within a finite bound when the owned child stops reading stdin. If the finish command cannot be delivered within `finish_timeout`, custody should retire only that owned child, preserve the timeout and retirement outcome in its receipt, and leave score/graceful completion unclaimed.

**T:** On the exact pre-fix V40 source, fill a non-reading child's stdin pipe and call `finish()` with a 50 ms finish timeout from a guarded thread. Preserve the first failure. Then apply a candidate repair and run the same regression plus the complete focused V40 suite, compilation, whitespace validation, and an independent source/output audit.

**D:** `PASS_BOUNDED_FINISH_DELIVERY_CONSTRUCTION` only if the baseline fails because `finish()` stays blocked past 350 ms, while the repaired candidate returns within that bound, requests termination of its owned child, records `finish_send_timeout`, leaves `finish_sent` and `score_observed` false, and leaves no live test child. Any hang, missing receipt, mistaken graceful-success claim, or child still running fails.

**C:** This host-only child process does not reproduce every runtime/backend's pipe behavior. Forced termination stops the owned process but does not prove an application-level release receipt or successful scoring.

**U:** The experiment uses a synthetic non-reading child and no game, model, GUI, physical input, WSLc allocation, or formal #59 lane. It proves bounded cleanup under this exact pipe-pressure construction only.

## Change

The finish message now runs on one daemon writer thread joined with `finish_timeout`. If delivery blocks or errors, custody terminates its own child and escalates to `kill()` only if the bounded wait expires. The cleanup receipt records `finish_send_timeout`, `child_termination_requested`, and `child_kill_requested`; it does not claim the finish command or post-control score succeeded. Stdin close is skipped while the writer remains blocked so cleanup does not re-enter a blocking stream operation.

## Evidence

`baseline-test-source.py.txt` is the exact regression source used for the initial red run. `baseline-test-output.txt` and its exit code retain the failure against the original controller at the PR base. The focused candidate run, full V40 suite, compile, diff check, source hashes, and independent audit are retained alongside. The prior V40 T0–T3 evidence and source identity discrepancy remain unchanged.
