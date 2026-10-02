# Pre-formal record — A04

Base main at intake and issue registration: `52c42c40bb074f46db1dc74afb20508e68bc1282`. Before the frozen package/PR, main advanced to `c17490cae4cb1e9600b816484f5103e3613700af`. Cumulative direct compare found only `.github/workflows/analysis-index.yml`, `RESEARCH.md`, `research/analysis/README.md`, and unrelated #6155/#6645 research evidence changed; `ROADMAP.md` and `docs/CURRENT_GOAL.md` remained unchanged and no A04 source/data/runtime path overlapped. Candidate, auditor, fixture, oracle, tests, and decision gates remained byte-identical. A03's report identified the exact mismatch this successor repairs: phase arms had unequal capture schedules and horizons.

Local construction: native Windows, standard-library Python only. `python -B -m unittest -v` passed 9/9. `python -B -m py_compile candidate.py auditor.py test_protocol.py` passed. Tests explicitly check phase-pair capture schedule, observation horizon, and expiry equality; expected hit/miss distinction; all boundary and UNKNOWN/N/A labels; independent audit; and five corruption controls. No formal candidate/auditor CLI invocation or output file was used during construction.

The auditor was reviewed before freeze to ensure it independently derives boundary/reason from timestamps, capture IDs, delivery, decision, receipt and horizon before checking the scoring-only oracle. It does not import the candidate. No WSLc/container/GPU process was started.

At freeze, candidate/audit output paths are required to be absent. After the branch/PR contains the exact frozen hashes, recheck current main, branch/PR ownership and output collisions; only then run the one-shot pair. Any changed frozen hash or occupied output path is STOP with no execution/retry.
