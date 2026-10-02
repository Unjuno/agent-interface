# Issue #2437 — backend-process crash with live Xvfb (Allocation 03)

Allocation: `X11-BACKEND-PROCESS-RESTART-2437-20261001-03`  
Freeze time: 2026-10-01, Asia/Tokyo  
State: preregistered; formal candidate not yet invoked. Allocations 01 and 02 remain separate STOPs and are not pooled.

## Delta from Allocation 02

The scientific hypothesis, main source dependencies, Xvfb/Tk environment and single failure boundary are unchanged. Only the candidate evidence-recording boundary changes: the fresh-session child receipt is merged through a pure helper; its dispatch monotonic timestamp is copied into the parent raw; explicit independent cleanup fields are written through a pure helper; and the auditor reports candidate exceptions even when other required keys are missing. Ten preformal construction tests now directly cover those helpers and the previously missing exception case. Allocation 02's raw will not be read or rerun.

## H / T / D / C / U

**H — Hypothesis.** If the X11 backend-owning process dies after an F8 key-down has been independently observed, while the Xvfb server remains the same live process, a newly created backend process/session may start without inherited quarantine and accept the same still-unexpired request carrying the old observation sequence and binding revision. If so, stale authority crosses a backend-process restart boundary while the key is still observed down.

**T — Minimum test.** On one private Xvfb server with the repository's Tk fixture: construct and retain one valid program before failure injection (`observation_seq=7`, `binding_revision=3`, 30-second monotonic lease); a child backend presses F8 and stays alive; an independent Xlib connection observes F8 down; SIGKILL only that backend process and verify its exit plus unchanged Xvfb PID; independently observe F8 still down; launch a second backend process/session and submit the byte-identical still-unexpired program without a new observation; record admission, session/process identities, dispatch time, emissions and independent keymap state; explicitly release F8 through the independent observer for cleanup. One candidate invocation, then one separate raw-only auditor invocation.

**D — Decision.** `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED` if request hash is identical, lease remains unexpired at dispatch, server PID is unchanged, old owner is killed with F8 independently observed down, and fresh session reports `recovery_required=false` yet completes the stale request with increased emissions. `PASS_BACKEND_RESTART_FAIL_CLOSED_SCOPED` only if replacement session starts quarantined, refuses with `INPUT_RECOVERY_REQUIRED`, emits zero input, and independent cleanup is verified neutral. Any missing identity, expired/mutated request, incomplete raw, failed cleanup, unexpected refusal, auditor/protocol deviation or nonzero child disposition is `STOP_*`, never favorable PASS.

**C — Competing explanations.** XTEST logical state can differ from physical hardware state; Xvfb is not a native compositor. Backend/session restart differs from X-server restart or synchronous pointer grabs. A separate Xlib connection is not an independent hardware sensor. The Tk fixture is inert to F8.

**U — Uncertainty / limits.** One WSL2 Ubuntu 24.04.4 x86_64 host, CPython 3.12.3, python-xlib 0.33, one private Xvfb and one F8 key. No Windows native input, physical device, compositor, production model, task quality or latency claim. Only backend-process death/replacement with X server alive; no supervisor death, host failure, multiple controls, delayed requests or real compositor.

## Frozen repository state and source identities

- `Unjuno/agent-interface` main: `d077494b50341f638e6d66f63e817ec48923768d`
- `runtime/backends/x11_v1/session.py`: `b81ca9b3a2c1d692e314ed8435db481cb6cc22ff6ad974148482787545c5bb62`
- `runtime/backends/x11_v1/backend.py`: `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`
- `runtime/backends/x11_v1/fixture_app.py`: `47ebb8ac9fb57cd318ffb3f0653aee9d3b10343d61b41bf2d6c9521f2af5e4ea`
- `runtime/core_v1/contract.py`: `4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2`
- `runtime/backends/x11_v1/test_integration.py`: `9ecdecb867c136079c9193aeab6b625f191c429da716a48f3c80b94ab3bf1560`
- `experiment.py`: `a8d1ac4122594e3e8dadbcb801b6e51211d458a637189651f55788f96435c227`
- `test_audit.py`: `9b0f076702182316f722e9346c4a71a50b22373c859a9dfe0230994a07b5d40d`
- `preflight.py`: `789500c4be84315d740f120852a0370cdcb4d167145ab8ae8cdbd43ee382807e`

## Execution gates

- Preformal construction: `test_audit.py` must pass all ten tests; a fresh no-input Xvfb/Tk preflight must show live server and fixture identities, 32-byte keymap, zero backend emissions. These are construction checks only.
- Immediately before formal, reread GitHub main and require exactly `d077494b50341f638e6d66f63e817ec48923768d`; reread #5085 and Docker inventory. The shared Docker CPU lane remains unassigned to this work; do not inspect/pull/build/launch any container. Use only private WSL Xvfb, no Docker claim.
- Output directory `/tmp/agent-interface-2437-backend-restart-d077494b-v3-20261001` must be absent. One candidate command:

```sh
xvfb-run -a -s "-screen 0 800x600x24" env PYTHONPATH=/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v3 python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v3/experiment.py --formal /tmp/agent-interface-2437-backend-restart-d077494b-v3-20261001/RAW.json
```

- After candidate exit, call `experiment.py --audit <RAW.json> --receipt <AUDIT.json>` exactly once. Raw SHA-256 is recorded during this single read. No other test, parse, candidate or auditor may read this allocation's raw afterward. Any failure is retained as STOP; no further allocation retry is authorized by this freeze.
- Additive evidence path `research/analysis/x11_backend_process_restart_2437_v3/`; branch `research/2437-backend-process-restart-xvfb-v3-20261001`. Do not edit runtime/shared paths or predecessor evidence.

## Preformal construction results

- Ten unit tests passed: the prior seven admission/negative-control cases plus direct dispatch-receipt merge, independent-cleanup receipt, and exception-reporting when required keys are also missing.
- No-input private-Xvfb/Tk preflight passed with a 32-byte keymap and backend emissions 0.
- Docker Desktop was last observed as `desktop-linux`, server `28.5.1 linux/amd64`; inventory empty. This is not a lease. #5085 still bars unassigned shared-container execution.
