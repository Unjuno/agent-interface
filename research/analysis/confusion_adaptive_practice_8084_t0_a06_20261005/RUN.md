# A06 execution record

- Freeze commit: `698b2af6ef40eb80eec62fa3b85dc328f1f07b45`; frozen source hashes are in `FREEZE.json`.
- Runtime: Windows x64, CPython 3.12.10, standard library only.
- Construction tests: 3/3 normal and 3/3 with optimization passed before freeze. One earlier construction test initially failed; retained in `results/construction-initial-failure.txt`.
- Fixture generator: invoked once, exit 0; 80,000 observations (8 profiles × 2 sample sizes × 5,000 replicates).
- Candidate: invoked once, exit 0; raw output retained in `results/candidate.stdout.json`; stderr empty.
- Auditor: one launch attempt, process did not start. `py -3` was not available in PowerShell. Exact error retained in `results/auditor-launch-error.txt`; no retry per frozen protocol.
- Inputs staged in auditor working directory: exact candidate stdout and frozen observed counts. No auditor stdout or scientific disposition exists.
- Runtime and participant/GUI/model claims: none. No container, WSLc, Docker, network, GPU, participant, GUI, or external data.

The STOP is an execution failure only. It does not support or refute H.
