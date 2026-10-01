# Prechecks and construction log

Allocation: `issue3555-xres-guard-orbstack-v2-formal-01` (see final outcome in `REPORT.md`).

## Environment

- OrbStack engine: 29.4.0, Linux/arm64.
- Pinned base: `agent-interface-3311-runtime-v2:20260920@sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`.
- Derived image contains Xvfb, XRes 1.2 client library, Python Xlib/Tk/Pillow, xdotool; formal execution is network-disabled.
- Additive path: `research/live_control/x11_xres_incarnation_guard_3555_v2/`.

## Construction dispositions

1. Initial image build attempted `python3 -m pip install ...`; STOP: pip is absent in the pinned image. The dependency was unnecessary (Python Xlib/Pillow already exist); removed the pip invocation. No formal allocation occurred.
2. First C helper used `spec.client=0` as an all-clients query, then tried per-client specs with combined XID/PID mask. XRes rejected those requests. Replaced lookup with the known usage pattern: locate the owning client via `XResQueryClients`, then query a window XID with PID mask. An early helper also omitted `XResQueryExtension`; that was corrected.
3. The decisive C bug was interpreting `XResQueryClientIds`'s `Status` as a boolean. Comparing with `Success` (0), consistent with XRes call sites, yielded the PID correctly. Verified in Xvfb that `xres_owner` reported the fixture's actual process PID. This was a construction diagnostic, not a formal allocation.
4. Construction-only process-restart probe under OrbStack Xvfb (network none) observed p1 `(pid=14, XID=2097156, start_ticks=265816)` then p2 `(pid=18, XID=2097156, start_ticks=265832)`. Geometry was `(0,0,240,160,24)` and both window pixel-buffer hashes were `12b331f398f2f4b8e7bf53b547095d742602058ea68d697a22380f55ce4922a1`. XRes returned the matching PIDs for both. This establishes the formal alias-reuse precondition for this fixture only.
5. `python3 -m unittest -v test_guard.py`: 3 passed. A first read-only-source py_compile check could not create `__pycache__`; rerun using `PYTHONPYCACHEPREFIX=/tmp/...` before formal freeze.
6. With the final button fixture, construction-only p1/p2 again reused the same XID and exact pixels (new image SHA `871bca1ba588f1ea184ea311181c785fc1843ac577a13427c74ee70647db3fb2`), with PID/start-tick changes and matching XRes PID. The first smoke harness translated coordinates in the reverse direction and reported `(-80,-80)`; corrected the runner to translate root origin into the window. This was a harness-coordinate error only; no input was sent.

## Required formal gates

- Freeze commit/source hashes, image digest/platform, OrbStack version, command, display, mounts/network, and output path before starting formal Xvfb.
- One formal allocation, no retries. Preserve raw stdout/stderr and `raw.json` exactly.
- Independently audit raw event rows and run corruption challenges. STOP before any input if reuse/geometry/pixel/PID/start-tick preconditions fail. If stale admission occurs, suppress the fresh positive control and retain FAIL.
- Confirm cleanup and button release. One scoped PASS does not establish product integration.

## Formal allocation audit invocation disposition

The first separate-container auditor CLI invocation returned only its usage string because the frozen CLI argument-count check expected the wrong `argv` length. It did not alter `raw.json`, launch input, or rerun the formal runner. The unchanged frozen audit implementation was then invoked through its Python `main(raw, freeze, output)` entry point in a second network-disabled container. That produced `PASS_INDEPENDENT_AUDIT`, zero errors, and rejected all three corruption controls. The initial invocation failure remains documented here; the successful audit is preserved as `artifacts/formal_01/audit.json`.
