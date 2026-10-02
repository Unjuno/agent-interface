# Issue #2437 — simultaneous held controls with pre-dispatch state receipt (Allocation 05)

Allocation: `X11-BACKEND-RESTART-MULTICONTROL-2437-20261001-05`  
Freeze time: 2026-10-01, Asia/Tokyo  
State: **preparation/preregistration only; Allocation 05 is not formally frozen or launched** because no shared Docker/OrbStack slot is assigned. Formal candidate invocations: 0; auditor invocations: 0. Allocations 01–04 remain separate STOP/inconclusive records; no pooling.

## Delta from Allocation 04

The scientific factor is unchanged: one backend process holds F8 and Button1, dies while Xvfb remains alive, and a new backend session receives the same stale request. The receipt boundary now captures `recovery_required` immediately before dispatch and again after dispatch in one helper. V4 recorded the so-called initial state only after dispatch, so when cleanup detected an untracked button and mutated recovery state, the raw could not discriminate admission from pre-existing quarantine. V5's construction unit test simulates exactly that state transition and asserts distinct before/after values. No V4 raw is read or rerun.

## H / T / D / C / U

**H — Hypothesis.** A backend-process crash with both F8 and left mouse button held can leave both controls logically down on a live Xvfb server; a fresh backend/session may accept the old still-valid request and emit keyboard input while the pre-crash pointer hold is not owned/tracked by that session.

**T — Minimum test.** Create one valid F8-chord program before failure (`observation_seq=7`, `binding_revision=3`, 30-second monotonic lease). An old backend child emits left-button-down and F8-down and stays alive. An independent Xlib connection observes both down. SIGKILL that child; require exit and unchanged Xvfb PID, then independently observe both controls still down. A distinct fresh process/session receives the byte-identical unexpired request with no new observation. Capture pre-dispatch recovery state before the call, dispatch result, post-dispatch recovery state, session identities, emissions and independent key/button masks. Explicitly release F8 and Button1 through the observer; verify both neutral. One frozen candidate invocation, then one raw-only audit invocation.

**D — Decision.** `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED_MULTICONTROL` if both controls are independently down before/after old-owner death, same Xvfb PID and distinct process/session identities hold, the unchanged request is unexpired, the fresh session's **pre-dispatch** recovery state is false, its dispatch is admitted (completed or execution-failed after admission), emissions increase, and independent cleanup returns both controls neutral. `PASS_BACKEND_RESTART_FAIL_CLOSED_MULTICONTROL` only if pre-dispatch recovery is true, dispatch refuses with `INPUT_RECOVERY_REQUIRED`, emits zero input, and cleanup independently verifies both controls neutral. Any missing/contradictory observation, unrelated refusal, identity/timing drift, failed cleanup, or audit/protocol error is `STOP_*`.

**C — Competing explanations.** XTEST/Xvfb masks are logical state, not physical hardware. Server restart, synchronous passive grab and native compositor are different boundaries. The independent observer is another X connection, not hardware instrumentation. An admitted execution failure is still an authority-boundary failure if it emitted stale input; it is not task success.

**U — Uncertainty / limits.** One WSL2 Ubuntu 24.04.4 x86_64 host, CPython 3.12.3, python-xlib 0.33, private Xvfb/Tk fixture, F8 plus left button. No physical devices, Windows native input, compositor, model, task-quality, latency or product claim. No supervisor/host death, delayed request, duplicate cleanup, or other control combinations.

## Preparation repository state and source identities (not an experiment freeze)

- `Unjuno/agent-interface` main: `dd1f9382ea20d15629516bb0dd995f4a4f1e4f32`.
- `runtime/backends/x11_v1/session.py`: `b81ca9b3a2c1d692e314ed8435db481cb6cc22ff6ad974148482787545c5bb62`
- `runtime/backends/x11_v1/backend.py`: `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`
- `runtime/backends/x11_v1/fixture_app.py`: `47ebb8ac9fb57cd318ffb3f0653aee9d3b10343d61b41bf2d6c9521f2af5e4ea`
- `runtime/core_v1/contract.py`: `4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2`
- `runtime/backends/x11_v1/test_integration.py`: `9ecdecb867c136079c9193aeab6b625f191c429da716a48f3c80b94ab3bf1560`
- `experiment.py`: `9bc5f7444f485817ae819515ba44827ee5e9c81553c4db98f0b0725092024d42`
- `test_audit.py`: `78094b98d54a8cf1666b33cb11519342ebfe8db990d8ee9ba6c5f30124b219cf`
- `preflight.py`: `789500c4be84315d740f120852a0370cdcb4d167145ab8ae8cdbd43ee382807e`

## Execution gates

- Preformal construction requires all 12 unit tests to pass (including the simulated pre-dispatch false → post-dispatch true recovery transition and explicit multicontrol schema rejection), plus a no-input fresh-Xvfb/Tk preflight with live identities, 32-byte keymap and zero emissions.
- Formal execution remains prohibited until the coordinator records an exact exclusive Docker/OrbStack assignment with owner, allocation, current-main SHA and start/end boundary. The latest #5085 state is request-only, not a grant. Immediately before any later freeze/launch, reread GitHub main, active owners, queue and inventory, then freeze a new exact allocation; do not reuse this preparation SHA if main or source changes. Do not inspect/pull/build/launch any container before grant.
- Proposed output directory `/tmp/agent-interface-2437-backend-restart-dd1f938-v5-20261001` was verified absent during preparation. If a future exact slot is assigned and all refreeze gates pass, a newly frozen command may use:

```sh
xvfb-run -a -s "-screen 0 800x600x24" env PYTHONPATH=/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v5 python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v5/experiment.py --formal /tmp/agent-interface-2437-backend-restart-dd1f938-v5-20261001/RAW.json
```

- If a future assigned allocation launches and the candidate exits 0, run its raw-only auditor once; it must record raw SHA-256 during that one read. No other candidate/test/parser/auditor may read raw afterward. For GitHub publication, use one-way opaque blob creation only and do not fetch/read back `RAW.json`. No retry of any consumed allocation.
- Additive path `research/analysis/x11_backend_process_restart_2437_v5/`, branch `research/2437-backend-restart-multicontrol-v5-20261001`.

## Preformal construction

- Eleven V4 construction tests and the V5 receipt-order test pass (12/12). V5 additionally rejects the prior single-control schema from the multicontrol auditor. Construction found two defects before any candidate launch: the synthetic fixture initially lacked the multicontrol schema (8/12 failed), and bundle review then found the candidate raw still declared the old schema. Both were corrected; the full suite was rerun (12/12 pass) and the no-input preflight passed.
- No-input private WSL Xvfb/Tk preflight on the candidate source reports 32-byte keymap and zero backend emissions. This is host construction evidence only, not Docker or formal-allocation evidence.
- Docker Desktop was previously observed as `desktop-linux`, version `28.5.1 linux/amd64`. Current shared-container inventory/ownership is unknown; latest #5085 comment #5917534571 is a request-only slot message and grants nothing. An empty inventory is not a lease.
