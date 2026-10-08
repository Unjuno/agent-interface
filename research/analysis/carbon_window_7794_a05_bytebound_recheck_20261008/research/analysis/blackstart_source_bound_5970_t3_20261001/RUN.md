# T3 run record

## Construction ledger before one-shot candidate

The exact outcomes below occurred before any candidate, Xvfb, or XTest input:

1. Construction attempt 1: four source-dependent tests failed because `source/app.py` and `source/observer.py` had not yet been reconstructed from Git blobs. One anchor-negative test passed. No archive member was extracted and no input ran.
2. Construction attempt 2: the transformer expected one observer event-writer anchor, but the frozen source contains two identical writers (normal event loop and explicit drain). The transformer failed closed; tests also exposed an invalid duplicate-anchor assertion.
3. Construction attempt 3: two negative-test predicates were incorrect; the corrected test exposed a sample oracle action-ID mismatch. The fixture was corrected, not the research protocol.
4. Final construction suite: 8/8 pass. Python compilation passes for candidate, runner, transformer, auditor, tests, and both generated sources. The archive was reconstructed in memory: digest `5f153824d677503275f268e2aef9c9971d5f0a3f369c573feaa1a5d10604ad8d`, 36,032 bytes, 324 regular files, 24 formal cases. Exact source hashes match `FREEZE.json`.

## Environment gate

- Docker Desktop/backend processes were present, but `com.docker.service` was `Stopped / Manual`; Docker CLI server version did not respond. Starting the service failed with access denied (`Cannot open 'com.docker.service' service`). No container could be started.
- WSL2 Ubuntu is running; `xvfb-run`, Python 3.12.3, Tk 8.6, Python-Xlib, and XTEST import successfully. Xvfb `-version` is unsupported, retained as a diagnostic response rather than interpreted as an engine/version check.
- No Xvfb process or user-desktop input is used during construction.

## Locked one-shot command

`python candidate.py` reconstructs the frozen source, verifies source hashes, deterministically emits the derived app/observer plus exact unified diffs, then runs `runner.py` once under `xvfb-run -a -s '-screen 0 1024x768x24'`. It sends one Shift press and unconditionally attempts the matching release in `finally`, then queries the virtual server keymap. `python audit.py` independently reconstructs the archive from Git blobs and adjudicates raw source records. Candidate and auditor may each run once; do not rerun either if output exists.

## Candidate v1 preflight STOP

`python candidate.py` ran once after the source/transform freeze and stopped before runner/Xvfb/input. Its `wsl.exe wslpath` invocation received a mangled `C:Users...` path because Windows native argument parsing removed backslashes. Preserved as `candidate.preflight_stop.raw.json`; no run directory was created and dispatch count is zero. The exact v1 source and FREEZE_T3 remain immutable. A separately frozen `candidate_v2.py` successor uses deterministic drive-letter conversion and a separate `run_v2/` output. This is a construction preflight STOP, not a scientific T3 event outcome.

## Candidate v2 and independent audit

- Start gate: `FREEZE_T3_V2.json` matched all 15 frozen analysis/source entries; `run_v2/` and `candidate.v2.raw.json` did not exist. The 8 construction tests passed and the generated app/observer compiled.
- Exact candidate command: `python research/analysis/blackstart_source_bound_5970_t3_20261001/candidate_v2.py` (one invocation). Candidate v2 verified candidate-v1's no-dispatch STOP, reverified the archive and exact source hashes, regenerated both frozen derivatives, then ran the driver once under a new private `xvfb-run -a` display.
- The app recorded one Shift `KeyPress` and one Shift `KeyRelease`, with expected X server times, keycode 50, source-local IDs, and action parents. Observer bootstrap succeeded, but it recorded zero key events. Runner therefore retained an incomplete-trace error; its unconditional cleanup sent the Shift release anyway. The final isolated X-server keymap reported `shift_down=false`. `run.raw.json`, `actions.jsonl`, app events, and observer events preserve the raw outcome.
- Exact independent audit command: `python research/analysis/blackstart_source_bound_5970_t3_20261001/audit.py research/analysis/blackstart_source_bound_5970_t3_20261001/candidate.v2.raw.json` (one invocation). It independently reconstructed the archive from Git blobs, confirmed digest/inventory and both archived source hashes, then returned `HOLD_SOURCE_BOUND_TRACE_INCOMPLETE`; errors are the expected observer event-set mismatch and runner's incomplete-trace error. No clock field was used to infer causality.
- Disposition: `HOLD_SOURCE_BOUND_TRACE_INCOMPLETE`, not a positive traceability pass. Candidate v1's WSL path STOP remains unchanged; no formal #4135 allocation was rerun.
