# R46 preparation

Attempt `win32-supervised-recovery-fresh-generation-task-20261024-r46-59e927d9c5884c7cb6d1d5f5980e35d0` is a new native-Windows one-shot, with unique attempt, task, oracle, program and lease IDs. It carries forward the strict R45/R44 standard-caller release-to-fresh-generation sequence and adds the exact effect-write timestamp sidecar.

R45 stopped 4.9554 ms below the frozen gate. The R45 post-hoc diagnosis found that CPython 3.11.9's `time.monotonic()` uses a 15.625 ms GetTickCount64 clock while the measured timestamps use 100 ns QueryPerformanceCounter. R46 uses `perf_counter_ns()` for the hold deadline and comparison, matching hook/audit timestamps, and plans 1,400 ms against the unchanged 1,250 ms minimum. Its maximum projected and callback ceilings remain 2,900 and 3,000 ms. The input-free preflight records actual clock implementation/resolution and checks the frozen clock contract.

Any gate failure is the first outcome; no retry, replacement, threshold weakening or second phase after a failed phase-1 gate.
