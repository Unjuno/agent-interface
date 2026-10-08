# MAP01 terminal-wait boundary discrimination — T4 result

Disposition: **PASS_WAIT_BOUNDARY_DISCRIMINATION_SCOPED**. This is a synthetic `JsonSession.wait()` boundary experiment, not a MAP01 recovery result.

## H / T / D / C / U

- **H:** Different terminal-event conditions can produce the same timeout exception when the child remains alive during the bounded wait.
- **T:** Loaded the unmodified current-main `JsonSession` implementation after verifying runner Git blob `f5caf71a743a563b7de046b82d44db7ebe49e829`. One candidate invocation launched four synthetic Python children: correct terminal within bound, wrong terminal ID, no terminal, and correct terminal emitted after the wait deadline. A separate auditor reconstructed each raw sidecar and checked exact IDs, timestamps, wait outcomes, hashes and cleanup receipts.
- **D:** Candidate exit 0; independent auditor exit 0; construction suite 4/4 passed; retries 0. The on-time exact ID returned. Wrong ID, no terminal, and late exact ID all produced precisely `TimeoutError: session event timeout`. The wrong ID was retained in the event trace; the absent case had no terminal; the late case retained the matching terminal after both the deadline and wait return. All four child processes were reaped and all reader threads joined. Intentionally terminated wrong-ID and absent children exited 1; the on-time and late children exited 0.
- **C:** Under this controlled helper, timeout text alone does not identify missing, mismatched, or late terminal delivery. A retained event stream with IDs and emission time can distinguish these synthetic conditions. The child processes and event stream are synthetic; no MAP01 child lifecycle or recovery action was exercised.
- **U:** The cause of the consumed #3202/#3211 timeout remains unknown. No evidence shows whether its recovery terminal was emitted, delayed, mismatched, dropped, or omitted from the artifact. No formal allocation, game, model/provider, GUI/input, GPU, container, or retry was used.

## Freeze, start gate, and execution

- Preparation freeze main: `bd77907946b7164e7513c3f5893f99348639e48a`.
- At the 2026-10-01 11:22:57 UTC start gate, remote main had advanced to `943b3942f33b62db31d4239302aac092e6d38f47`; the target runner blob was still exactly `f5caf71a743a563b7de046b82d44db7ebe49e829`, matching the local imported file. No matching branch or open PR was found.
- `python -B -m unittest -v test_construction.py`: **4/4 passed**; frozen input hashes verified before candidate execution.
- `python -B candidate.py --out results/t4-01`: one invocation; four isolated synthetic child cases; exit 0.
- `python -B audit.py --repo-root ..\\..\\.. --out results\\t4-01`: one independent invocation; exit 0; `AUDIT.json` retains `PASS_WAIT_BOUNDARY_DISCRIMINATION_SCOPED`.
- Candidate sidecars preserve the source runner's historical literal-`\\n` separator. The independent parser reconstructs those raw objects without interpreting the file as conventional JSONL; T2/T3 separately tested that formatting defect.

## Docker Desktop / resource stop

Read-only Docker Desktop UI at the start gate displayed **Engine running**, zero running containers, 39 existing inactive container entries, 5.15 GB Engine RAM, 67.06% Engine CPU and 21.10/1006.85 GB disk. `docker context show` reported `desktop-linux`; both the default and explicit `desktop-linux` server-version probes timed out. Windows `com.docker.service` reported Stopped/Manual despite the UI's Engine-running state. Issue #5085 comment #5930107044 assigned the 11:20–11:30 UTC CPU OrbStack window to a different task; this task had no transferred slot. No image build/pull, container creation/start, cleanup, or service change occurred.

This is an **infrastructure/authority stop for container execution**, not a scientific FAIL. The host-only test was intentionally kept small and isolated; it does not replace the requested container-level preflight.

## Integration boundary

This result narrows what `TimeoutError("session event timeout")` can mean, but it does not identify which explanation occurred in #3202/#3211. Any repair or formal follow-up still requires a fresh, owner-bound allocation and raw recovery-arm event retention. See `FREEZE.json`, `START_GATE.json`, `candidate.json`, and `SHA256SUMS` for provenance.
