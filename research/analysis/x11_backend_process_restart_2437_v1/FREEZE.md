# Issue #2437 — backend-process crash with a live Xvfb server

Allocation: `X11-BACKEND-PROCESS-RESTART-2437-20261001-01`  
Freeze time: 2026-10-01, Asia/Tokyo  
State: preregistered; formal candidate not yet invoked.

## H / T / D / C / U

**H — Hypothesis.** If the X11 backend-owning process dies after an F8 key-down has been independently observed, while the Xvfb server remains the same live process, a newly created backend process/session may start without inherited quarantine and accept the same still-unexpired request carrying the old observation sequence and binding revision. If so, stale authority crosses a backend-process restart boundary while the key is still observed down.

**T — Minimum test.** On one private Xvfb server with the repository's Tk fixture: (1) construct and retain one valid program before failure injection (`observation_seq=7`, `binding_revision=3`, 30-second monotonic lease); (2) a child backend presses F8 and stays alive; (3) an independent Xlib connection observes F8 down; (4) SIGKILL only that backend process and verify its exit plus unchanged Xvfb PID; (5) independently observe F8 still down; (6) launch a second backend process/session and submit the byte-identical still-unexpired program without a new observation; (7) record admission, per-process emissions and independent keymap state; (8) explicitly release F8 through the independent observer for cleanup. Run the frozen candidate once and the raw-only auditor once. The auditor must not be run on construction fixtures or again after formal.

**D — Decision.** `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED` if the old request hash is identical, its lease is unexpired at dispatch, the display server PID is unchanged, the old owner was killed with F8 independently observed down, and the fresh session reports `recovery_required=false` yet completes the stale request with increased backend emissions. `PASS_BACKEND_RESTART_FAIL_CLOSED_SCOPED` only if the replacement session starts quarantined, refuses with `INPUT_RECOVERY_REQUIRED`, emits zero input, and independent cleanup is verified neutral. Any missing identity, expired/mutated request, incomplete raw, failed cleanup, unexpected refusal, auditor/protocol deviation or nonzero child disposition is `STOP_*`, never a favorable PASS.

**C — Competing explanations.** XTEST logical key state can differ from physical hardware state; Xvfb is a simulated server, not a native desktop compositor. A process/session restart may have different semantics from X-server restart or synchronous pointer grabs. The separate observer is an independent X connection, not an independent hardware sensor. The Tk fixture is deliberately inert to F8.

**U — Uncertainty / limits.** One WSL2 Ubuntu 24.04.4 x86_64 host, CPython 3.12.3, python-xlib 0.33, one private Xvfb and one F8 key. No Windows native input, physical device, compositor, production model, task-quality or latency claim. This tests only backend-process death/replacement with the X server kept alive; it does not cover supervisor death, host failure, multiple held controls, delayed requests or a real compositor.

## Frozen repository state and sources

- `Unjuno/agent-interface` main: `d1dc9b8e6cc1e165d353f086b530a0024277b7f6`
- `runtime/backends/x11_v1/session.py` SHA-256: `b81ca9b3a2c1d692e314ed8435db481cb6cc22ff6ad974148482787545c5bb62`
- `runtime/backends/x11_v1/backend.py` SHA-256: `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`
- `runtime/backends/x11_v1/fixture_app.py` SHA-256: `47ebb8ac9fb57cd318ffb3f0653aee9d3b10343d61b41bf2d6c9521f2af5e4ea`
- `runtime/core_v1/contract.py` SHA-256: `4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2`
- `runtime/backends/x11_v1/test_integration.py` SHA-256: `9ecdecb867c136079c9193aeab6b625f191c429da716a48f3c80b94ab3bf1560`
- `experiment.py` SHA-256: `53317c669bbdd02d86615f08a36cd8cd5bdfc76b66114cddb5d8662bdbd746e0`
- `test_audit.py` SHA-256: `2b1908028a7bfc18f77cc6bca5d0b0b6f23364f4881961aff5bdfa701015e565`
- `preflight.py` SHA-256: `789500c4be84315d740f120852a0370cdcb4d167145ab8ae8cdbd43ee382807e`

## Execution gates

- Construction only: `test_audit.py` covers pristine FAIL classification, an explicit fail-closed PASS, wrong-refusal STOP, incomplete input, and key/server/cleanup mutation detection. A no-input `preflight.py` on a fresh Xvfb must show a live server PID, live Tk fixture, 32-byte keymap, and zero emissions.
- Immediately before formal invocation, re-read GitHub main and require the exact frozen SHA above; re-read #5085 and Docker inventory. The shared Docker CPU lane is not assigned to this allocation (#5074 retained its slot; later queue requests remain requests without a lease). Do not inspect/pull/build/launch a Docker image or container under that queue state. This allocation therefore uses private WSL Xvfb and makes no Docker result claim.
- Formal output directory `/tmp/agent-interface-2437-backend-restart-d1dc9b8e-20261001` must not exist before launch. One candidate command only:

```sh
xvfb-run -a -s "-screen 0 800x600x24" env PYTHONPATH=/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001 python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001/experiment.py --formal /tmp/agent-interface-2437-backend-restart-d1dc9b8e-20261001/RAW.json
```

- After the candidate exits, invoke `experiment.py --audit <RAW.json> --receipt <AUDIT.json>` exactly once. It reads the raw once, records the raw SHA-256 while reading, and writes the receipt. No other test, parse, candidate, or auditor may read `RAW.json` afterward. Preserve a command/setup failure as STOP and do not retry this allocation.
- Publish through an additive path `research/analysis/x11_backend_process_restart_2437_v1/` and a unique branch `research/2437-backend-process-restart-xvfb-20261001`. Do not edit runtime/shared paths or predecessor evidence.

## Construction record (pre-formal)

- Seven auditor construction unit tests passed before formal.
- A separate no-input Xvfb/Tk preflight passed with Python-Xlib 0.33, a 32-byte keymap and backend emissions 0. No candidate key or pointer operation was invoked by preflight.
- Docker Desktop context observed as `desktop-linux`, server `28.5.1 linux/amd64`; active container inventory empty at the check. Neither observation is a lease; #5085 forbids using an unassigned shared container slot.
