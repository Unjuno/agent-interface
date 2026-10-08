# Issue #6147 T0 allocation 02 — terminal STOP

The finite safe-probe candidate did **not** yield a method result. It exited 1 after writing raw output, when the final summary referenced a nonexistent field. Status is `STOP_CANDIDATE_RUNTIME_ERROR / NOT_EVALUATED`; no auditor ran and no retries are allowed. The raw file is immutable evidence of the first process output, not an audited result.

- [Frozen H/T/D/C/U and exact sources](FREEZE.md)
- [Terminal STOP report](STOP.md)
- [Unverified raw candidate output](RAW.json)
- [Process record](RUN_RECORD.json)
- [SHA-256 manifest](SHA256SUMS.txt)
- [Candidate source](candidate.py)
- [Independent auditor source (not invoked)](audit.py)

Host CPython 3.11.9; CPU-only; standard library. No container, GUI, game, model, GPU/CUDA, network, or physical input was used. Scope remains strictly an implementation failure; there is no hypothesis verdict or runtime/product evidence.

