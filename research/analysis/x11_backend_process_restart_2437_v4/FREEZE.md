# Issue #2437 — backend restart with simultaneous held key + button (Allocation 04)

Allocation: `X11-BACKEND-RESTART-MULTICONTROL-2437-20261001-04`  
Freeze time: 2026-10-01, Asia/Tokyo  
State: preregistered; formal candidate not yet invoked. Allocations 01–03 are separate, non-pooled records (see Draft PR #5618).

## Delta from Allocation 03

Scientific factor: the crashed X11 backend owner now holds both F8 and left mouse button simultaneously. Independent Xlib state samples must establish both controls down before and after SIGKILL while the same Xvfb PID stays alive. The replacement process receives the same pre-created F8-chord request. Its terminal release may release only state tracked in the replacement backend session; whether the orphaned button remains down is separately sampled. This is not a rerun of the single-key allocation.

## H / T / D / C / U

**H — Hypothesis.** A backend-process crash with both a key and pointer button held can leave both controls logically down on a live Xvfb server; a fresh backend/session may accept the old still-valid request and emit keyboard input while the pre-crash pointer hold is not owned/tracked by that session.

**T — Minimum test.** Create one valid F8-chord program before failure (`observation_seq=7`, `binding_revision=3`, 30-second monotonic lease). An old backend child emits left-button-down and F8-down and stays alive. An independent Xlib connection observes both down. SIGKILL that child; require its exit and the same Xvfb PID, then independently observe both still down. A distinct fresh backend process/session receives the byte-identical unexpired request with no new observation. Capture dispatch/admission, session identities, emissions and independent key/button masks. Explicitly release F8 and Button1 on the observer connection; require both independently neutral. One frozen candidate invocation and one raw-only audit invocation only.

**D — Decision.** `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED_MULTICONTROL` if both controls are independently down before/after old-owner death, the same server PID and distinct process/session identities are verified, request hash is unchanged and unexpired, the fresh session is not quarantined, its dispatch is admitted (completed or execution-failed after admission) and emissions increase, and explicit independent cleanup returns both controls neutral. `PASS_BACKEND_RESTART_FAIL_CLOSED_MULTICONTROL` only if the replacement starts quarantined, refuses with `INPUT_RECOVERY_REQUIRED`, emits zero input, and independent cleanup verifies both controls neutral. Missing/contradictory observations, unrelated refusal, identity/timing drift, failed cleanup or protocol error is `STOP_*`; never favorable PASS.

**C — Competing explanations.** XTEST/Xvfb key/button masks are logical server state, not physical hardware sensing. Server restart, synchronous passive grab and a native compositor are separate boundaries. The independent observer is a second X connection only. A failed terminal cleanup after admission is not alone evidence of task success or a physical stuck control.

**U — Uncertainty / limits.** One WSL2 Ubuntu 24.04.4 x86_64 host, CPython 3.12.3, python-xlib 0.33, private Xvfb/Tk fixture, one F8 and left button. No physical mouse/keyboard, Windows native path, compositor, model, task-quality, latency or product claim. Does not cover supervisor/host death, delayed requests, duplicate cleanup or multiple buttons/keys beyond this pair.

## Frozen repository state and sources

- `Unjuno/agent-interface` main: `19c588c063fec0cc46ccda5d0154a5984afcb6c1`.
- `runtime/backends/x11_v1/session.py`: `b81ca9b3a2c1d692e314ed8435db481cb6cc22ff6ad974148482787545c5bb62`
- `runtime/backends/x11_v1/backend.py`: `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`
- `runtime/backends/x11_v1/fixture_app.py`: `47ebb8ac9fb57cd318ffb3f0653aee9d3b10343d61b41bf2d6c9521f2af5e4ea`
- `runtime/core_v1/contract.py`: `4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2`
- `runtime/backends/x11_v1/test_integration.py`: `9ecdecb867c136079c9193aeab6b625f191c429da716a48f3c80b94ab3bf1560`
- `experiment.py`: `ad22e0699a9bdf76272e9fd957a7b67391f4059c49574330f5fcb774a183cc63`
- `test_audit.py`: `bde2c5247959145b5082e2e1af0ba83ab3369f5c50bf0f17ee8f488937f781cd`
- `preflight.py`: `789500c4be84315d740f120852a0370cdcb4d167145ab8ae8cdbd43ee382807e`

## Execution gates

- Preformal construction requires all 11 `test_audit.py` unit tests to pass and a no-input Xvfb/Tk preflight with a live server/fixture, 32-byte keymap and zero backend emissions.
- Immediately before formal, re-read GitHub main and require exact `19c588c063fec0cc46ccda5d0154a5984afcb6c1`; refresh #5085 and Docker inventory. This task has no shared Docker/OrbStack lease. Do not inspect/pull/build/launch a container; use private WSL Xvfb only.
- Output directory `/tmp/agent-interface-2437-backend-restart-e918dff-v4-20261001` must be absent. Formal command, one invocation:

```sh
xvfb-run -a -s "-screen 0 800x600x24" env PYTHONPATH=/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v4 python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v4/experiment.py --formal /tmp/agent-interface-2437-backend-restart-e918dff-v4-20261001/RAW.json
```

- After formal exit, call the frozen raw-only auditor exactly once with `--audit <RAW.json> --receipt <AUDIT.json>`. It records the raw SHA-256 during its one read. No other candidate/test/parser/auditor may read raw afterward. Publish via one-way opaque blob creation only; **do not fetch/read back RAW.json**. Preserve GitHub blob SHA from create response; any inability to publish safely is a delivery STOP.
- Additive path `research/analysis/x11_backend_process_restart_2437_v4/`, branch `research/2437-backend-restart-multicontrol-v4-20261001`. No runtime/shared path edits. No retry of Allocation 04.

## Preformal evidence

- Eleven unit tests passed, including both-control retention and stale-admission classification plus mutation/cleanup/identity/expiry controls.
- No-input Xvfb/Tk preflight passed: 32-byte keymap, `backend_emissions=0`.
- Docker Desktop last observed as `desktop-linux`, server `28.5.1 linux/amd64`; active inventory empty. This is not a lease. #5085 queue's latest request is request-only/withdrawn; no allocation is transferred here.
