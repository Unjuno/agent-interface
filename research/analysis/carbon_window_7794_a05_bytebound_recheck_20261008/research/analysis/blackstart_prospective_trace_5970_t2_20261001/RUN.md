# Run record — Issue #5970 T2 / T2b / T2c

## Environment and setup

- Repository branch base frozen at `98bc3eb7051bfb18292f6526e2e33f1e2e96e762`; archived experiment source commit pinned at `7625a3fc99f1da2099dc6e20e67383ee88c7f337`.
- Docker check: `Get-Service com.docker.service` reported `Stopped / Manual`; Docker Desktop's Linux WSL distro was stopped and `docker version` could not connect. The installed Docker Desktop engine switch request did not produce a usable daemon. No container was started or borrowed.
- Isolated fallback: WSL2 Ubuntu 24.04.4 LTS, Python 3.12.3, Tk 8.6, Xvfb package 21.1.12, `python-xlib` and XTEST. `xvfb-run -a` creates a private virtual display; no user desktop or physical input path is used.
- Frozen archive preflight: the five base64 part hashes and compressed archive digest match `FREEZE.json`; the tar contains 425 entries, of which 324 are regular files and 101 directories.
- Construction before the live attempt: `python3 -m unittest -v` — 11 passed; `python3 -m py_compile candidate.py independent_audit.py candidate_v2.py independent_audit_v2.py candidate_v3.py independent_audit_v3.py runner.py runner_v3.py instrumented_app.py instrumented_observer.py test_audit.py test_t2c_construction.py` — passed. Frozen source and prior-attempt hashes matched.
- Source-boundary note: candidate v3 executed the purpose-built `instrumented_app.py` / `instrumented_observer.py` pair, not a mechanical patch of the archived #4135 `app.py` / `observer.py`. Their archive hashes were verified as reference context only. See `METHOD_DEVIATION.md`; no transfer to the original observer is claimed.

## Exact candidate attempts

Commands below were executed from this package directory through WSL:

1. `python3 candidate.py` — exit 1, `STOP_CANDIDATE_PREFLIGHT_INVENTORY_PREDICATE`. The implementation compared the frozen regular-file count (324) to all tar entries (425). It stopped before creating `run/`; no Xvfb or input started. Preserved as `candidate.preflight_stop.raw.json`.
2. `python3 candidate_v2.py` — exit 1, runner timeout while polling the wrong app-log path. The app and observer each wrote an `arm_ack`; no `dispatch_request` exists in the action stream, so no key event was sent. The corrected inventory preflight verified 324 files and 425 total members. Preserved under `candidate.v2.raw.json` and `run_v2/`.
3. `python3 candidate_v3.py` — exit 1 with candidate disposition `HOLD_INCOMPLETE_OR_NONNEUTRAL`. Both arm acknowledgements precede one `KeyPress` dispatch. The app log at `run_v3/trace/tk/app_events.jsonl` contains one matching `KeyPress` and explicit `act:<actuation_id>` parent. The observer log contains the arm acknowledgement but no matching key event. The driver stopped on timeout; no `KeyRelease` was dispatched, and no terminal keymap was queried. The run's Xvfb process had exited by the post-run process check; the virtual display was isolated and torn down.

The exact STOPs and the incomplete live trace are preserved; there was no rerun of candidate v1, candidate v2, candidate v3, or the #4135 formal allocation.

## Independent audit

- `python3 independent_audit_hold.py` — executed once, exit 0, `PASS_AUDIT_HOLD_OBSERVER_EVENT_MISSING`, zero errors.
- It independently reconstructed the archived source inventory and compared candidate summaries against raw app, observer, and driver JSONL. It verified the first two no-dispatch STOPs; for T2c it found one app event, zero observer events, one dispatched press, zero releases, and no verified terminal keymap. It did not infer edges from timestamps.
- Audit inputs and auditor source are pinned in `AUDIT_FREEZE_V3.json`; output integrity is pinned in `AUDIT_RESULT_FREEZE.json` and `SHA256SUMS.txt`.
