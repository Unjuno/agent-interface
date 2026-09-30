# Issue #5370 T6: nested inheritance and fairness boundary

Disposition: `STOP_PROTOCOL_DEVIATION`. The frozen candidate ran once, but final verification evaluated the frozen raw with both the valid-fixture unit test and a second standalone audit after the preregistered audit had already passed. All returned no errors, but the one-audit limit was exceeded. The raw bytes did not change. The synthetic finding is preserved but is not an accepted PASS. This does not close Issue #5370, Issue #59, or a runtime/roadmap gate.

- Preregistered hypothesis and decision gates: [PLAN.md](PLAN.md)
- Frozen analysis and limitations: [REPORT.md](REPORT.md)
- Commands, exits, raw/source identities: [RUN_LOG.md](RUN_LOG.md)
- Candidate discrete-event replay: [scheduler.py](scheduler.py)
- Independent raw-only oracle: [audit_raw.py](audit_raw.py)
- Candidate/oracle tests: [test_scheduler.py](test_scheduler.py), [test_audit.py](test_audit.py)
- One-shot raw: [results/formal-01/raw.json](results/formal-01/raw.json)
- Audit outputs and protocol deviation: [results/formal-01/AUDIT_RECEIPTS.md](results/formal-01/AUDIT_RECEIPTS.md)
- Bundle integrity: [SHA256SUMS.txt](SHA256SUMS.txt)

No Docker invocation occurred; the shared local container lane was not explicitly assigned to this T6 allocation.
