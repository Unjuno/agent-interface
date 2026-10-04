# Issue #7722 T0 — replenishable CPU service

This package records the first frozen, CPU-only scheduler simulation for [Issue #7722](https://github.com/Unjuno/agent-interface/issues/7722). The independent auditor reconstructed all service events and rejected all six frozen mutations (`METHOD_PASS_SCOPED`); the scientific gate failed (`FAIL_HYPOTHESIS`) because the reserved server still missed control deadlines in each schedulable trace.

The result is useful negative evidence about this Qc/Pc allocation: p99 improved by 71–77%, but a 5-tick rolling control budget did not cover every fixed-seed adjacent-arrival pattern. It does not establish that reservations are unnecessary or that real CPU contention delays release. No tuning or rerun followed the retained first result.

## Contents

- `PROTOCOL.md`: H/T/D/C/U, units, thresholds, model and scope.
- `cases.json`: exact fixed-seed schedulable, negative, overload and replenishment-boundary traces.
- `freeze.json`: main base, image, requested resources, invocation count and frozen source hashes.
- `candidate.py`, `auditor.py`: separate deterministic scheduler and independent raw-event verifier.
- `output/candidate/`: untouched candidate raw JSON, stderr, WSLc logs, CID and elapsed-time metadata.
- `output/auditor/`: untouched independent audit result, stderr, WSLc logs, CID and elapsed-time metadata.
- `REPORT.md`, `RUN.md`, `RESULT.json`: interpretation, reproduction and compact outcome.
- `SHA256SUMS`: checksums for every retained file except the checksum list itself.

## Verification

Run `python verify_retained.py` to check the frozen inputs, raw/audit hashes, recorded exit codes, run matrix and audit disposition without launching either formal process again. The one candidate and one auditor invocations are not repeatable allocations.
