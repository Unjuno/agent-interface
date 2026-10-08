# Construction and environment record

Allocation `8638-T0-A02-20261009`; formal candidate/auditor counts at freeze: 0/0.

## Preserved A01 boundary

Issue #8638 A01's candidate and auditor each ran once in one isolated V8 tool session and returned `PASS_METHOD_SCOPED`, but the tool projected only summary fields and did not retain its complete 48-row JSON. This is an artifact-custody STOP, not a scientific failure. A01 is not rerun or relabeled. A02 is a fresh allocation with a new 13-case input, new candidate/auditor programs, and separate output paths.

## A02 construction outcomes

- Initial pre-freeze audit source compared fraction strings with Python's default zero formatting (`0` versus the candidate's canonical `0/1`). It rejected the exact-zero holdout despite matching rows. This construction defect was fixed before freeze using one explicit rational formatter; the defective auditor source was not part of the frozen package.
- After that correction, the independent audit reconstructed the construction candidate's 192 rows with zero errors. A later pre-freeze audit version also independently recomputed mutual information, acquisition-only net value, all three pair values, and rankings.
- Six mutation checks all failed closed: dropped attempt row, changed hidden truth, authority escalation, forged consumption receipt, stale-signal promotion, and forged pair ranking (`construction_report.json`).
- `python3 -B -m py_compile candidate.py auditor.py construction_check.py` passed under Python 3.14.5.
- Candidate and independent auditor both completed successfully under the frozen macOS network-deny profile during construction. A separate loopback connection probe returned `PermissionError: [Errno 1] Operation not permitted`.
- `docker context ls` identified the OrbStack context and server version 29.4.0. The read-only `docker --context orbstack ps` request failed before listing containers with a containerd content-blob error (`operation not supported`). No container was started, stopped, removed, or modified. The issue's finite exact CPU enumeration needs no image or container, so the documented fallback is the native deterministic process under the tested `sandbox-exec` network-deny profile. This is not Docker/OrbStack execution evidence.
- A generic `python3 -B -m unittest discover -v` from the package found zero test modules and exited 5; this package's meaningful construction checks are `construction_check.py` and `py_compile`, both of which passed. No test suite was claimed from the empty discovery command.

## Decision before formal run

The formal source, inputs, commands, output names, no-retry rule, and decision criteria are pinned in `FREEZE.json` and `PROTOCOL.md`. Candidate and auditor will each run at most once in fresh `raw/` paths. Any incomplete raw write, nonzero candidate exit, hash mismatch, or missing independent reconstruction ends the allocation as a retained STOP/HOLD/FAIL; there will be no same-allocation repair or retry.
