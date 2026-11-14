# WSLc ViZDoom MAP01 target startup smoke — 2026-11-15

## Result

**A03 PASS_TARGET_STARTUP_NO_INPUT.** A fresh WSLc 3.0.5.0 container using the local image digest `sha256:f439b660f68c58b01dba6bf28b0e55f4df3cd8ed55570fe026b1df760d8f7063` started the bundled ViZDoom engine and Freedoom `MAP01` under a private Xvfb display. The initial screen buffer was 640×480; the engine exposed initial `AMMO2=50`; the episode remained active; Python/import-to-state took 751.5 ms; `game.init()` took 290.8 ms and `new_episode()`-to-state took 430.2 ms, derived from the retained phase timestamps. The IWAD hash was `729f100448d0b48e12ecc8004e096a9ea6df024467d962f002bb286805be3a8e`. The game closed normally and the command exited 0. No input event was sent.

The engine and IWAD are available inside WSLc, so this host can run a new isolated **Linux/Xvfb ViZDoom** MAP01 task. This does not locate or launch Windows `gzdoom.exe`.

## Attempt ledger

| Attempt | Outcome | Evidence |
|---|---|---|
| A01 | `FAIL_PREINPUT_CONTAINER_INIT`, exit 1. The read-only bind at `/study` hid the image work directory `/study/SOURCE`; runc failed before Python or the game started. | `conditions.json`, `stdout.raw.txt`, `stderr.raw.txt`, `exit-code.txt` |
| A02 | `FAIL_PREINPUT_STARTUP_TIMEOUT`, exit 137. The game process made no progress output for about 30 seconds. A bounded stop of this uniquely owned container escalated after 3 seconds; `--rm` then removed it. No input was sent. | `conditions-a02.json`, `stdout-a02.raw.txt`, `stderr-a02.raw.txt`, `exit-code-a02.txt` |
| A03 | `PASS_TARGET_STARTUP_NO_INPUT`, exit 0. A phase-logging run under an explicit 12-second timeout completed all startup and normal-close phases. The container was unique and removed on exit. | `conditions-a03.json`, `diagnostic_smoke_map01.py`, `stdout-a03.raw.txt`, `stderr-a03.raw.txt`, `exit-code-a03.txt` |

A03 differs from A02 by moving the read-only mount away from the image workdir, adding unbuffered phase records, and imposing a 12-second timeout. The A02 container was never restarted or reused. All three attempts used network `none` and one CPU; no Docker command or old container was used for this WSLc smoke.

The conditions record the default WSLc CLI context observed before the attempt; commands did not pass `--session`. A later read-only `wslc info` snapshot reported session 1, so the packet does not claim a stable numeric session identity. It also does not claim isolation from concurrent WSLc users beyond the observed empty running-container set before launch.

## Scope and next discriminating step

This is an environment/target construction result only. The test bypassed agent-interface and used no external input. It proves neither a key-down/key-up pair nor input release, delayed-input exclusion, expiry cancellation, bounded runtime recovery, HUD effect after a task action, task success, provider cost, nor efficiency. It is not native Win32 evidence and does not close the open computer-control objective. A next WSLc experiment should use the exact current-main caller against this fresh MAP01 target, capture full-resolution before/after frames and a separate release receipt, and retain a hard process bound. The independent native Win32 path still requires a Windows GZDoom target; none was found in the inspected Windows/Steam paths or current process inventory.

## Reproduction and custody

Run the checked-in A03 script once, as captured by its conditions, with the locally cached image digest and a new unique container name. The raw stdout/stderr and exit codes are retained without normalization. `commands.txt` retains the exact argv for all attempts. `audit.py` independently verifies the stop classes, A03 phase order, scope, and manifest membership. `SHA256SUMS` covers all evidence files except itself. The pinned image was inspected read-only; no pull/build occurred. Docker Desktop remains running but its stored containers are stopped. No prior WSLc/Docker container was restarted.
