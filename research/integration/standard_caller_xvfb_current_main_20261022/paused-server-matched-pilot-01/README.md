# Matched private-Xvfb server-pause pilot

**Run ID:** `AI-XVFB-PAUSED-SERVER-MATCHED-PILOT-20261022-01`
**Source:** current main `cc5ef16c560cc985ee0951d3d53d659e892f5167`
**Environment:** Ubuntu 24.04 WSL2; Python 3.12.3; a fresh private Xvfb `:88` per trial. No WSLc/Docker allocation.

## Result

All six candidate tests passed (1/1 each), all six Xvfb processes exited zero, and the post-series process check found no Xvfb left running. The three control and three paused trials all passed the frozen admission-based composite: response within 300 ms of the server admission timestamp, pending/UNKNOWN fence preserved, bounded terminal receipt, independent release readback, no old delayed press through the 8.5 s horizon, distinct fresh target/session/process generation, and synthetic fresh-task oracle pass. The old canceled operation remained UNKNOWN, `task_success=null`, and replay-denied in every trial.

| Pair | Control admission → response | Paused admission → response | Paused duration | Supervisor readback after resume | Independent readback after resume |
|---|---:|---:|---:|---:|---:|
| C01 / P01 | 255.418 ms | 253.263 ms | 1,500.340 ms | 54.800 ms | 127.834 ms |
| C02 / P02 | 256.398 ms | 253.738 ms | 1,500.320 ms | 59.460 ms | 101.874 ms |
| C03 / P03 | 254.895 ms | 254.955 ms | 1,500.300 ms | 59.700 ms | 117.030 ms |

The measured `cancel_started`-to-return interval was 256.920–258.156 ms in controls and 308.533–309.810 ms in paused trials. This is **not** end-to-end caller latency: the timestamp occurs before test setup and a deliberate 50 ms wait used to verify that Xvfb is stopped; the code does not timestamp immediately before `server.call_tool`. Actual caller invocation-to-return latency is therefore unqualified. The admission-based handler deadline is the only caller timing that this pilot directly qualifies.

The fresh-task oracle verified the independent synthetic effect, but the test does not timestamp the exact effect readback. Observation/effect timing still needs instrumentation at the public call boundary and independent effect readback. The per-trial audit and raw SHA-256 manifests preserve the distinction. Three pairs are a small pilot, not broad reliability evidence; no model/token accounting or matched efficiency was measured.

This experiment shows the public caller's admitted cancellation remains responsive during one private Xvfb process pause, with release and independent key-up readback after service resumes. It does not prove release while X11 is stopped, host-wide I/O recovery, physical GUI/MAP01 behavior, or WSLc portability. Results remain scoped to this fixture, schedule, machine and source.
