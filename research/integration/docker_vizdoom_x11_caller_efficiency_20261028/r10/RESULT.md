# R10 result: Docker/Xvfb direct vs compiled caller path

All four preregistered arms passed every task-effect and release gate. In both pairs, direct and compiled each produced +122.6285 map units on X and the effect receipt was bound to the observed action. Independent X11 samples saw W down during dispatch and W up after return; backend release receipts were verified with no keys/buttons held.

| Pair | Seed | Direct (ms) | Compiled (ms) | Compiled minus direct | Relative |
|---|---:|---:|---:|---:|---:|
| 1 | 2026102911 | 878.530 | 917.770 | +39.240 ms | 4.47% slower |
| 2 | 2026102912 | 877.520 | 901.310 | +23.790 ms | 2.71% slower |

Across these two pairs, the direct median was 878.0265 ms and the compiled median was 909.541 ms: a +31.5145 ms difference, or 3.59% slower for compiled. This is a tiny descriptive sample, not a reliability or general performance estimate. The timed path includes fresh in-path observation, the 600 ms key hold, guarded dispatch, one post-release ViZDoom synchronization tick, and the typed effect check. It excludes startup and alias mint/preflight. No model/provider/MCP calls, token counts, or billing were involved. It is not end-to-end model efficiency.

R9 established the oracle correction: after the guarded action, ViZDoom's position did not become observable to the callback until one `advance_action(1, True)` tick. The R10 perception callback drains exactly one such tick after keyboard return, then evaluates the position predicate. R4/R6/R7/R8 failed to make a valid effect determination because they read before this tick; R5 did not launch due the read-only current directory. Those historical packets remain unchanged and are not pooled with R10.

The four arm `result.json` files and native bridge observation/execution/release/image artifacts are retained under `arms/`. `PRETRIAL_SHA256SUMS` freezes the source harness, conditions, preregistration, and image identity. `POSTTRIAL_SHA256SUMS` hashes the entire packet after the trials. Docker ran with network disabled, read-only root filesystem and source mount, writable evidence mount, `/tmp` tmpfs and cwd. The Docker wrapper's final cleanup fragment was incorrectly quoted by PowerShell, so Docker CLI returned exit 2 after Python had completed and written each passing `result.json`; no arm was retried. Raw Python result artifacts, not the wrapper exit status, determine the preregistered gates.

Scope: local Docker Desktop Linux Engine, Xvfb, ViZDoom 1.3 / FreeDoom MAP01. This says nothing about Windows/WSLc transfer, delayed-operation recovery, MAP01 completion, broad reliability, model/token savings, or product-level efficiency.
