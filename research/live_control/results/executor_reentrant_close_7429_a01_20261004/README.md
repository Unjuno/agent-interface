# PR #7429 reentrant close-after-accept probe (A01)

## H / T / D / C / U

- **H:** If the synchronous accepted-event sink reenters `Executor.close()` while `Executor.submit()` holds its reentrant lock, #7429 may return from close while the worker is unstarted, then unconditionally start it when the sink returns. The close path sets the lease cancellation flag, so the worker should skip `Backend.execute`; the probe checks whether cleanup still runs after close returned.
- **T:** A fake backend and synchronous sink call `close()` from the `accepted` callback. The fake backend blocks in `release_all()` so post-close worker lifetime is observable. Compare the latest source with the pre-close-handling source. No Xlib or task I/O is imported by the harness.
- **D:** Reproduced if `close()` returns with `worker.ident is None`, then `submit()` starts a worker that remains alive in cleanup after close returned while `Backend.execute` stays uncalled.
- **C:** This is conditional on a synchronous emitter calling back into executor lifecycle methods. The repository does not establish that the production sink reenters `close()`, so this is a lifecycle contract gap, not evidence of current production impact.
- **U:** Host Python scheduling; no container because of the recorded OrbStack image-inspection STOP; no native backend/Xlib/device/game/model, production event transport, or broader concurrency stress. The fake backend makes no input calls.

## Frozen identities and execution

Source change under review: [PR #7429](https://github.com/Unjuno/agent-interface/pull/7429).

- Current `main`: `c9a02437e8565b340464ed9cde736fa9e5642ab4`.
- Current PR #7429 head: `8f6d92cd2f8bd1081b047bc272f10ff900bb2026`.
- A03 executed against conflict-free tree `e3542601e0f734dc89ba9fc5d16ae28abe1e46b5` at PR head `609dfb2`. Latest conflict-free main+PR tree is `973e4b0b49b2bb9fe279394f979173feea2ebea2`. Seven imported modules are byte-identical to the A03 snapshot. The latest `executor_v12.py` differs only by removal of one blank CRLF line at EOF; `REFRESH-CHECK-02.txt` records exact blobs and byte comparison after stripping terminal CR/LF. No executable code changed, so the candidate was not rerun.
- `source/current/` is the exact A03 executed snapshot; latest PR source bytes are pinned by the commit/blob identities above.
- Pre-close-handling source commit: `1efc8897ed6c48b9c57e1f03efbf4f69bc900cd4`; the control shows the prior `close()` error, not a current PR parent.
- Candidate runtime: host CPython 3.14.5.
- A02 reproduction: `PYTHONPATH=source/a02 python3 candidate-a02.py`.
- A03 reproduction: `PYTHONPATH=source/current python3 candidate-a03.py`.
- Parent control: `PYTHONPATH=source/parent python3 control-parent.py`.

A01 had a harness error after the worker completed: its final assertion dereferenced `executor.active` after the worker had correctly cleared it. Its raw exit 1 is retained; no result is taken from that assertion. The corrected A02 on head `e22e597` passed; its complete imported source closure is retained under `source/a02/`. A03 then ran against exact refreshed merge-tree source `e3542601` and also exited 0: `close()` returned while the worker had no thread identity, then `submit()` started it; it remained alive inside fake `release_all()` after close returned. `Backend.execute` was not called because the lease had been canceled. The pre-close-handling control exited 0 after observing `RuntimeError: cannot join thread before it is started`; that worker stayed unstarted and `execute` was not called.

OrbStack's `python:3.12-slim` preflight stopped at `docker image inspect` with an unsupported content-store blob error. No Docker run, image pull, or alternate runtime was attempted. Host execution is retained separately and is not container-qualified.

This deterministic result applies only to a synchronous reentrant emitter. It does not establish that the production event sink reenters `close()`, exercise actual backend cleanup/input, or qualify release publication, task feedback, bounded recovery, live allocation, or useful game effect.
