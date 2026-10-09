# One-shot execution record

- Allocation: `5311-T0-A01-20261009`
- Current-main anchor: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`
- Freeze/preregistration commit: `6031647b1f0221616f1131d4669c1d90cc165f1f`
- Runtime: CPython 3.14.5, arm64, macOS 27.0.1
- Docker inspection: Docker 29.4.0 daemon responded, but image inspection failed with containerd content-blob `operation not supported`; host-only execution was used under this issue's stdlib/offline scope. No container isolation claim.
- Construction suite: `python3 -m unittest -v test_construction.py` passed 2/2 before freeze.
- Candidate command, once: `python3 candidate.py cases.json results/candidate.json` — exit 0.
- Auditor command, once: `python3 auditor.py cases.json results/candidate.json results/audit.json` — exit 0, 15 rows, zero errors.
- Retries or post-freeze edits to frozen inputs/source: zero.
- Disposition: `FAIL_COST_GATE_SCOPED`; see [REPORT.md](REPORT.md).

Raw streams and exact exit codes are retained under `results/`. The auditor independently reconstructed the admitted predicate/effect outcomes and independently checked the declared inspection counts. All result paths and hashes are listed in [SHA256SUMS](SHA256SUMS).
