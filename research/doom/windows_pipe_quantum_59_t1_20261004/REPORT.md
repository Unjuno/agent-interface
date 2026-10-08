# Windows pipe polling quantum comparison — Issue #59 construction T1

## Preregistered question and decision

The frozen hypothesis asked whether a 1 ms `PeekNamedPipe` polling sleep beats 5 ms on readiness tail latency while keeping CPU under 1% during a 28.57 ms idle wait. `FREEZE.json` was written before data collection and fixes the trial counts, seeded order, metrics, and decision rule.

The decision is **HOLD**. The paired p95 improvement (5 ms minus 1 ms) was 4.902 ms, clearing the 1 ms latency threshold. The 1 ms idle arm consumed 7.88% process CPU, failing the strict `<1%` cost gate. The 5 ms arm consumed 1.42% in the same short sample. The rule required both latency and CPU gates, so it does not support adopting or recommending 1 ms from this construction.

## Execution and evidence

Ran on native Windows 11 build family `10.0.26200`, CPython 3.12.10. The runner used real `os.pipe()` anonymous pipes and `PeekNamedPipe`, with 128 paired seeded delayed-write trials per arm and 70 idle timeouts per arm. Pair order was shuffled using the preregistered seed. Both arms also passed EOF readiness/read-empty smoke checks. The independent audit recomputes the summary from `results/raw.csv`, verifies paired delays and arm quanta, checks byte/EOF/timeout outcomes, and validates the frozen candidate source and raw CSV SHA-256 values.

| Measure | 1 ms | 5 ms |
|---|---:|---:|
| Readiness p95 | 1.641 ms | 5.500 ms |
| Idle CPU / wall | 7.88% | 1.42% |
| Idle samples | 70 | 70 |

Paired per-delay median improvement was 2.080 ms; the preregistered paired p95 improvement was 4.902 ms. Raw measurements and the machine/result manifests are in `results/`.

## Scope and limitations

This is a local synthetic pipe measurement, not a Doom/game, WSL, live controller, or task-effect run. Timer/scheduler state and the host affect these measurements. The idle CPU window is about 2.2 seconds per arm and is short; `process_time_ns` is visibly quantized on this host (reported CPU increments of 15.625 ms), so exact CPU percentages are coarse. The 1 ms arm nevertheless missed its bound by a wide margin in this sample. No production source was changed by this experiment.

## Reproduction

From the repository root on native Windows:

```powershell
python research/doom/windows_pipe_quantum_59_t1_20261004/quantum_probe.py --out research/doom/windows_pipe_quantum_59_t1_20261004/results
python research/doom/windows_pipe_quantum_59_t1_20261004/audit.py
```
