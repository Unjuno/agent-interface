# Construction-clock-35 — engine stdout syscall mismatch

Disposition: `STOP_ENGINE_TIC_LINES_NOT_TIMESTAMPED`; no phase conclusion.

## H / T / D / C / U

- **H:** an `LD_PRELOAD` wrapper on libc `write(2)` can timestamp ViZDoom
  `VIZ_Tic` stdout lines using the same Linux `CLOCK_MONOTONIC` as Python.
- **T:** same pinned Linux/arm64 ViZDoom 1.3.0/Freedoom 0.13.0 image and
  hidden MAP01 `ASYNC_SPECTATOR` 35 Hz construction fixture as run 32. Three
  fresh sessions, each with a 1.5 s passive interval and one unchanged scorer
  call; `+viz_debug 2`, no controller actions or OS input. A C `LD_PRELOAD`
  wrapper timestamps stdout `write` calls and `stdbuf -oL` line-buffers engine
  output.
- **D:** compare monotonic prefixes on the exact scorer markers and on
  `VIZ_Tic` engine records; retain raw scorer clock traces, binary, wrapper
  source and full stdout.
- **C:** all three sessions/scorer calls/cleanup succeeded; Python-visible tic
  stayed 1 and the engine emitted internal tic lines. Python marker writes
  received `CLOCK_MONOTONIC_NS` prefixes, but ViZDoom engine tic lines did not.
  Therefore the wrapper missed the engine's actual stdout syscall path.
- **U:** the logger does not timestamp engine tic events. The cross-clock phase
  remains unobserved. Do not count the apparent unprefixed engine line order as
  a same-clock witness or combine this run with a phase allocation.

Reason: `STOP_INTERPOSER_MISSED_ENGINE_WRITEV_PATH`. The distinct writev-aware
wrapper is tested only in later run 36; this capture and its binary are
immutable.
