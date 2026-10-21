# Public-MCP prestarted cancellation supervisor — r01

## Result

This local Windows/Fake X construction run passes the focused owned-process,
guarded MCP, cancellation-supervisor and XRes-fence suites: **105/105 tests in
normal Python and 105/105 under `-O`**. The raw stdout/stderr, exit codes,
frozen conditions, source hashes and three sanitized public-caller trial
receipts are retained in [`r01/`](r01/README.md). The blocked-helper retirement assertion was explicitly added and rechecked in [`r02/`](r02/README.md). Duplicate cancellation identity in the opt-in path was separately asserted in [`r03/`](r03/README.md).

The later [`r04/`](r04/README.md) regression archives terminal receipts before
dropping their payload from the call's in-memory record. Public result retrieval
and post-terminal duplicate cancel still return the same receipt. A separate
injected write failure retains the terminal result in memory and does not start
a second cleanup. The focused suites pass 106/106 in normal and optimized
Python. This bounds live in-memory cancellation custody; terminal files remain
under the existing per-call artifact retention.

The [`r05/`](r05/README.md) response-shape check removes internal archive marker
fields from public call records while preserving the cancellation subrecord.
The focused suites again pass 106/106 in normal and optimized Python.

R06/R07 expose the opt-in through the standard MCP stdio CLI. R06 records one
normal-mode test error under concurrent Windows process scheduling and a clean
107/107 optimized run; the failing existing cancellation test passes alone.
R07 reruns the full focused suite and passes 107/107 in both modes. The CLI
still defaults the flag off and rejects it unless owned-process mode is set.

R08 reruns the four focused deterministic Fake X modules on the local
parent-owned PID-source correction. It passes 108/108 in normal and optimized
Python; conditions, all four test-module and relevant implementation hashes,
raw stdout/stderr, and exit codes are retained in [`r08/`](r08/README.md).
The Fake X result alone did not qualify the corrected source against live Xvfb.

The corrected-source [local Ubuntu WSL/Xvfb attempt](xvfb-local-wsl-20261022-r01/README.md)
reached the real blocked Display.sync and constructed the corrected owner PID
fields, but then failed closed when XRes saw PID 439 at the retired owner's
resource base. Cancellation returned in 43.659 ms and the heartbeat's maximum
gap was 5.800 ms; release remained UNKNOWN, the a obligation remained, and no
post-horizon readback or task oracle ran. The final harness cleanup is not
cancellation-release evidence. The full first outcome, raw report, conditions,
source hashes, and local runner are preserved separately.

The opt-in public MCP composition started one supervisor during owned-session
startup, before the test admitted input. In the healthy Fake X arm, cancel
response took 110 ms, the independent JSON oracle recorded exactly one
`KeyRelease`, and the key state became up. The stale-generation arm recorded
one refusal and no release. In the blocked-helper arm, cancel returned pending
in 313 ms, the event loop continued to service heartbeats, the absolute
transaction deadline elapsed, the helper was retired (`worker_retired=true`, asserted through the public caller), and the Fake X state
remained down/UNKNOWN. The standalone supervisor test independently asserts
that a blocked worker is retired at its deadline.

Across all arms, runtime `release_confirmed` stayed false, `task_success` stayed
null, cleanup stayed `UNKNOWN`, and replay stayed denied. The 110 ms and 313 ms
measurements are individual construction trials, not latency distributions or
production guarantees.

## Conditions and reproduction

`r01/conditions.json` freezes the local-run conditions and pass/fail rules;
`r01/source-hashes-at-run.txt` binds the code and test definitions. Reproduce
with:

```powershell
python -B -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_xres_client_fence
python -B -O -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_xres_client_fence
```

The sanitized per-arm JSON records are `healthy-release.json`,
`stale-generation.json` and `blocked-helper-deadline.json`. They omit local
paths, session identifiers and PIDs while preserving timings, status, effect
counts and the independent Fake X state decision.

## Limits

This is not a WSLc allocation or run. It does not run the production X11 worker
against Xlib or Xvfb; the public composition injects a deterministic Fake X
supervisor target. It does not prove that an X server drains already queued
requests, rejects a request that was issued before the deadline but processed
later, or that global keymap state belongs exclusively to this owner. It does
not establish hard process-termination bounds, physical release, blocked-live-
server release, task success, bounded post-outage recovery, MAP01, model/provider
integration, efficiency or reliability. The opt-in flag remains off by default.

A pre-freeze development run failed before the acceptance run: 67 of 104 tests
errored because the new opt-in arguments reached the non-owned owner constructor
and fixture-created owners lacked the new supervisor attribute. Those defects
were fixed before r01 conditions/source hashes were frozen. The initial console
output was not captured as a complete file and is not presented as raw evidence;
the failure summary is retained here for context only.

R04 does not cap disk retention. It also does not add finite retention for the
general `calls` history, which predates this cancellation slice.
