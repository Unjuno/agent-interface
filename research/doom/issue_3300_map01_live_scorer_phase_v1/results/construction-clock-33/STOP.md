# Construction-clock-33 — cross-clock phase calibration stop

Disposition: `STOP_CLOCK_DOMAINS_UNCALIBRATED`; no scorer-to-engine phase
conclusion. This run is excluded from formal allocation and from phase
distribution estimates.

## H / T / D / C / U

- H: test whether Docker's timestamped engine `VIZ_Tic` stdout can be aligned
  with the Python scorer-call trace closely enough to identify which internal
  35 Hz tic phase overlaps `_coherent_progress_sample`.
- T: OrbStack Linux/arm64, pinned ViZDoom 1.3.0 image
  `sha256:4320dd483b24ea91c1481f12fd5799c903d9daa99a517b994f607037098ea41d`,
  official Freedoom 0.13.0 WAD
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
  Six fresh hidden MAP01 `ASYNC_SPECTATOR` sessions, 35 Hz, empty buttons,
  no actions, 1.5 s passive windows, and one exact scorer call per session.
  The probe emitted Python `time.monotonic_ns()` and `time.time_ns()` values;
  Docker `logs --timestamps` supplied host-side RFC3339 timestamps.
- D: require a validated mapping between the container's monotonic clock,
  container wall clock, and Docker host timestamp before assigning engine
  tic records to scorer-call intervals.
- C: setup, scorer and cleanup succeeded 6/6; the Python API tic stayed 1.
  Docker supplied timestamps for every `VIZ_Tic` line, but no independently
  measured clock-domain offset/drift or synchronization error bound exists.
  The Docker host timestamp cannot be compared directly with the container's
  monotonic trace. The requested phase assignment therefore fails its gate.
- U: the visible internal tic lines remain diagnostic only. This run does not
  establish phase coverage or validate the requested six phase offsets; their
  targets were delays from a per-session Python monotonic start, not measured
  engine-phase targets. Preserve this STOP rather than infer synchronization.

## Evidence

- `raw.json` SHA-256: `833e3672b99446106117b73d0fd7a51f4cacd3b2dc6f826dbd31e84c1b8dd849`
- `container-timestamps.log` SHA-256:
  `d55400e272d7b7ec4048d0f295a573244145c980bf79573c94106fcf062dee80`
- Probe SHA-256:
  `4ae6ec6eb2e47daa0adb0df4503706157b729c3dc87568a63368dac78bf8fa22`
- Exact Docker invocation, host/image/WAD identifiers, and stdout capture
  procedure are in `invocation.txt`.
- All six scorer calls returned; all six games closed; zero advancing API calls.

No files from the earlier run were rewritten. `construction-clock-32` remains
the separate, instrumented evidence for internal tic progress with Python API
snapshot staleness, but does not resolve live scorer phase.
