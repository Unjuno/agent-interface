# Construction-clock-36 — LD_PRELOAD did not observe engine writes

Disposition: `STOP_INTERPOSER_NOT_OBSERVING_ENGINE_STDOUT`; no phase result.

## H / T / D / C / U

- **H:** adding a libc `writev(2)` wrapper as well as `write(2)` will capture
  timestamp prefixes on ViZDoom's child engine `VIZ_Tic` output, in the same
  Linux `CLOCK_MONOTONIC` domain as Python.
- **T:** run 32's three-session construction probe, same pinned arm64
  ViZDoom 1.3.0 / Freedoom 0.13.0 image and fixture; `LD_PRELOAD` injects the
  write/writev wrapper into the Python invocation; stdout is line-buffered.
- **D:** compare prefixed Python markers, scorer raw monotonic traces, and
  engine `VIZ_Tic` stdout. Retain the actual loaded library, compiler image,
  full log and raw capture.
- **C:** all 3 sessions initialized, exact scorer returned 3/3, cleanup 3/3,
  and API tic remained 1. Python parent writes received timestamp prefixes.
  The captured log contained engine `VIZ_Tic` records but zero of them carried
  a prefix. The shared-clock engine witness gate therefore failed.
- **U:** available evidence does not distinguish whether the engine child
  drops `LD_PRELOAD` or emits via an un-interposed syscall path. This run does
  not timestamp engine tics, calibrate scorer phase or authorize formal data.

Reason: `STOP_ENGINE_STDOUT_NOT_INTERPOSED`. The first write-only prototype is
separately preserved at `../construction-clock-35/`; neither capture has been
overwritten.
