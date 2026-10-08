# Issue #8473 — scoped infeasibility feedback T0 A02

A02 is a fresh allocation after A01 stopped before formal invocation because main advanced after freeze. It preserves A01 unchanged and tests the same finite hypothesis on exact current main with a new allocation ID, freeze, path, and branch. Candidate and auditor source, finite fixtures, oracle, and test construction are byte-identical to A01; the only protocol delta is the updated main/base/allocation provenance.

- H/T/D/C/U and one-shot commands: [PREREGISTRATION.md](PREREGISTRATION.md)
- Freeze and source hashes: [FREEZE.json](FREEZE.json), [SHA256SUMS.txt](SHA256SUMS.txt)
- Outcome: [REPORT.md](REPORT.md)
- Exact formal outputs: formal_01/RAW.json, audit_01/AUDIT.json
- Invocation/environment record: [RUN_RECORD.json](RUN_RECORD.json)

Method evidence is confined to the authored symbolic finite state space. A01 STOP remains at the predecessor path and is not relabeled.
