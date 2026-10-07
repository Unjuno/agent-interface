# Issue #8049 A03 — fresh-seed bootstrap coverage

`PASS_METHOD_SCOPED` for the frozen synthetic two-stratum design. The OrbStack
candidate and independent raw-only auditor each ran once; retries were zero.
The complete result and limitations are in [REPORT.md](REPORT.md).

- Protocol and H/T/D/C/U: [PROTOCOL.md](PROTOCOL.md)
- Frozen source/input/image identities: [FROZEN.json](FROZEN.json)
- Single-shot commands and exit receipts: [RUN_RECORD.json](RUN_RECORD.json)
- Independent audit: [audit.json](results/audit-out/audit.json)
- Preflight, construction-test, and main-advance history: [CONSTRUCTION_LOG.md](CONSTRUCTION_LOG.md), [MAIN_ADVANCEMENT.md](MAIN_ADVANCEMENT.md)
- File hashes: [SHA256SUMS](SHA256SUMS)

This is one synthetic population, one seed, and one interval recipe. It does
not establish distribution-free coverage, production verifier calibration,
GUI behavior, or action/safety authority. A02's pre-container CLI STOP and
A01's method failure remain preserved as predecessor evidence.
