# Issue #2437 — backend-process crash with live Xvfb (Allocation 02)

Allocation: `X11-BACKEND-PROCESS-RESTART-2437-20261001-02`  
Freeze time: 2026-10-01, Asia/Tokyo  
State: preregistered; formal candidate not yet invoked. Allocation 01 remains STOP; its outcome is not pooled.

## H / T / D / C / U

**H — Hypothesis.** If the X11 backend-owning process dies after an F8 key-down has been independently observed, while the Xvfb server remains the same live process, a newly created backend process/session may start without inherited quarantine and accept the same still-unexpired request carrying the old observation sequence and binding revision. If so, stale authority crosses a backend-process restart boundary while the key is still observed down.

**T — Minimum test.** On one private Xvfb server with the repository's Tk fixture: construct and retain one valid program before failure injection (`observation_seq=7`, `binding_revision=3`, 30-second monotonic lease); a child backend presses F8 and stays alive; an independent Xlib connection observes F8 down; SIGKILL only that backend process and verify its exit plus unchanged Xvfb PID; independently observe F8 still down; launch a second backend process/session and submit the byte-identical still-unexpired program without a new observation; record admission, session/process identities, emissions and independent keymap state; explicitly release F8 through the independent observer for cleanup. One frozen candidate invocation and one separate raw-only auditor. The auditor must not be run on construction fixtures or again after formal.

**D — Decision.** `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED` if request hash is identical, lease remains unexpired at dispatch, server PID is unchanged, old owner is killed with F8 independently observed down, and the fresh session reports `recovery_required=false` yet completes the stale request with increased emissions. `PASS_BACKEND_RESTART_FAIL_CLOSED_SCOPED` only if the replacement session starts quarantined, refuses with `INPUT_RECOVERY_REQUIRED`, emits zero input, and independent cleanup is verified neutral. Any missing identity, expired/mutated request, incomplete raw, failed cleanup, unexpected refusal, auditor/protocol deviation or nonzero child disposition is `STOP_*`, never favorable PASS.

**C — Competing explanations.** XTEST logical state can differ from physical hardware state; Xvfb is not a native compositor. Backend/session restart differs from X-server restart or synchronous pointer grabs. A separate Xlib connection is not an independent hardware sensor. The Tk fixture is inert to F8.

**U — Uncertainty / limits.** One WSL2 Ubuntu 24.04.4 x86_64 host, CPython 3.12.3, python-xlib 0.33, one private Xvfb and one F8 key. No Windows native input, physical device, compositor, production model, task quality or latency claim. Only backend-process death/replacement with X server alive; no supervisor death, host failure, multiple controls, delayed requests or real compositor.

## Frozen repository state and source identities

- `Unjuno/agent-interface` main: `d077494b50341f638e6d66f63e817ec48923768d`
- The main change from Allocation 01 (`#5617`, CI checkout/evidence only) leaves every listed dependency file SHA-256 unchanged.
- `runtime/backends/x11_v1/session.py`: `b81ca9b3a2c1d692e314ed8435db481cb6cc22ff6ad974148482787545c5bb62`
- `runtime/backends/x11_v1/backend.py`: `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`
- `runtime/backends/x11_v1/fixture_app.py`: `47ebb8ac9fb57cd318ffb3f0653aee9d3b10343d61b41bf2d6c9521f2af5e4ea`
- `runtime/core_v1/contract.py`: `4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2`
- `runtime/backends/x11_v1/test_integration.py`: `9ecdecb867c136079c9193aeab6b625f191c429da716a48f3c80b94ab3bf1560`
- `experiment.py`: `53317c669bbdd02d86615f08a36cd8cd5bdfc76b66114cddb5d8662bdbd746e0`
- `test_audit.py`: `2b1908028a7bfc18f77cc6bca5d0b0b6f23364f4881961aff5bdfa701015e565`
- `preflight.py`: `789500c4be84315d740f120852a0370cdcb4d167145ab8ae8cdbd43ee382807e`

## Execution gates

- Construction only: seven auditor unit tests cover stale-admission FAIL, explicit fail-closed PASS, wrong-refusal STOP, incomplete input, and key/server/cleanup mutation detection. A no-input fresh-Xvfb `preflight.py` must show a live server PID and Tk fixture, 32-byte keymap, zero emissions.
- Immediately before formal, re-read GitHub main and require exactly `d077494b50341f638e6d66f63e817ec48923768d`; re-read #5085 and Docker inventory. Docker CPU lane remains unassigned to this work (#5074 retained the assigned slot and newer queue requests are requests only). Do not inspect/pull/build/launch any container under that queue state. This allocation uses private WSL Xvfb and makes no Docker result claim.
- Output directory `/tmp/agent-interface-2437-backend-restart-d077494b-20261001` must be absent before launch. One candidate command:

```sh
xvfb-run -a -s "-screen 0 800x600x24" env PYTHONPATH=/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001 python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001/experiment.py --formal /tmp/agent-interface-2437-backend-restart-d077494b-20261001/RAW.json
```

- After candidate exit, call `experiment.py --audit <RAW.json> --receipt <AUDIT.json>` exactly once. The raw-only auditor reads the raw once and records SHA-256 during that read. No other candidate, test, parse, or auditor may read `RAW.json` afterward. Preserve any invocation/setup error as STOP; no retry of Allocation 02.
- Additive research path: `research/analysis/x11_backend_process_restart_2437_v2/`; branch: `research/2437-backend-process-restart-xvfb-v2-20261001`. Do not edit runtime/shared paths or predecessor evidence.

## Prior construction evidence (before both allocations)

- Seven auditor construction unit tests passed.
- No-input private-Xvfb/Tk preflight passed, reporting a 32-byte keymap and backend emissions 0.
- Docker Desktop was observed as context `desktop-linux`, server `28.5.1 linux/amd64`; inventory empty. Neither is a lease. #5085 forbids this unassigned shared container lane.
