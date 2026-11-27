# MAP01 native public-caller startup/readback diagnostic R27–R29

**Date:** 2026-10-26

**Runtime source:** `b62eed22eda49c7f76813930492c53326fd45391` plus the local single-target empty-obligation observer fix used only in R29

**Resource:** user-authorized native Windows GZDoom/Freedoom PC; no WSLc, Docker, model, provider, or input-down event

## Findings

- **R27 — UNKNOWN.** The single public dispatch was canceled 1.986 s after start-gate authorization, before a child-stage marker appeared. Same-host R17–R19 trials each measured child readiness 10.203 s after `Process.start`; this makes Windows spawn startup the likely reason the child did not reach its target function before cancellation. R27 has no child marker, so that causal explanation is probable rather than proven. Its GZDoom PID and UNKNOWN custody remain retained.
- **R28 — UNKNOWN.** A fresh-generation child became ready 10.512 s after `Process.start`, completed a no-input dispatch in 41.575 ms, exited 0, and wrote a verified release receipt with zero emissions. Public custody still became UNKNOWN because the independent observer rejected the empty obligation list before generation readback (`normal_completion_observer_receipt_invalid_or_late`).
- **Fix.** For normal completion observation only, `_observe` now uses the sole configured target when there are no key/button obligations, then validates that target generation before and after the empty state sample. Empty-obligation recovery remains refused. The helper/owner/public-MCP regression set passed 56/56 normally and 56/56 under Python 3.13 `-O`.
- **R29 — scoped pass.** On a new PID and target generation with the fix active, the public caller retained `completed` and `release_confirmed=true`. The producer exited 0, its verified neutral receipt had no down or unknown keys/buttons, and the independent observer returned a neutral readback bound to the exact operation and generation 8.625 ms after the producer-exit witness. This was a zero-input operation; `task_success` remains null.

R27 and R28 processes/outcomes were preserved without further calls. Only the R29 process was terminated, after the public caller confirmed release. This series does not demonstrate a task effect, MAP01 success, blocked-I/O recovery, a hard startup bound, or reliability. Exact private raw replies, producer progress/result packets, server reports, executable hashes, and process evidence remain in the local `private-packets/map01_native_windows_20261026_r27` through `..._r29` folders and are not duplicated in this public result.
