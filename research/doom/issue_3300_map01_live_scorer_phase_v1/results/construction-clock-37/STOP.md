# Construction-clock-37 — stdout buffering coarsened engine event times

Disposition: `STOP_ENGINE_TIC_WRITES_BUFFERED`; no phase conclusion.

## H / T / D / C / U

- **H:** `strace -f -ttt` on the pinned ViZDoom container records engine-child
  `VIZ_Tic` output writes in the same container wall-clock domain as Python
  `time.time_ns()`, allowing conversion to Python `time.monotonic_ns()` via
  repeated paired anchors.
- **T:** dedicated Linux/arm64 derivative image adds only Debian `strace`
  6.1-0.1 to the pinned ViZDoom 1.3.0 image. Three fresh hidden MAP01
  `ASYNC_SPECTATOR`, 35 Hz sessions; 1.5 s passive windows; exact scorer once
  each; no action, OS input, display or network. The probe brackets paired
  realtime/monotonic anchors every 50 ms. `strace -f -ttt -T` records only
  `write`/`writev` syscalls with 4096-byte strings.
- **D:** check child engine write PID, write timestamps, tic text, raw paired
  clock anchors, session/scorer/cleanup state and retained hashes.
- **C:** ptrace succeeded; all sessions/scorers/cleanup succeeded 3/3; raw
  API tic stayed 1. However, the engine child emitted large stdio-buffered
  writes (including chunks up to 4096 bytes) containing many `VIZ_Tic` lines.
  The syscall timestamp locates the buffer flush, not each contained tic
  event. These chunk timestamps cannot reconstruct individual tic edges or
  their phase against the scorer.
- **U:** realtime/monotonic calibration is present, but the engine-event
  timestamp granularity is insufficient because stdout buffering remains.
  No live phase distribution is claimed; formal allocation stays 0/120.

Reason: `STOP_ENGINE_TIC_WRITES_BUFFERED`. A line-buffered follow-up is a
separate run and must demonstrate one syscall per tic before phase matching.
