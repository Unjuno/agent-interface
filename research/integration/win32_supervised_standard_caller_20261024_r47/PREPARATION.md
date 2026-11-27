# R47 preparation

Attempt `win32-supervised-recovery-fresh-generation-task-20261024-r47-1eabc91d59e3488ca08e33f43297b6d6` is a new native-Windows one-shot, with unique attempt, task, oracle, program and lease IDs. It carries the same-clock finite recovery gate and fresh-generation task-oracle test forward from R46.

R46 phase 1 passed 11/11 strict release checks. Phase 2 never opened the fixture: the harness passed a `.py` path to `python -m`, causing CPython `ModuleNotFoundError` before CUA, observation, or task input. R47 changes this one harness defect to direct script invocation and otherwise retains the preregistered bounded protocol. It does not replay R46; all raw evidence lives in its original immutable packet.

This is still a local Windows fixture test. WSLc/Docker, MAP01, efficiency, reliability and transfer claims are excluded. One dispatch/cancel attempt in phase 1, phase 2 only after strict pass, no retry or replay.
