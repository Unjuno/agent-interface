# Issue #5927 — allocation-03 report

Disposition: **`PASS_METHOD_SCOPED`**. The frozen positive save/modal case required one fresh `persistence_receipt` exchange; the common-safe-action null control required zero. A separate raw-only v2 auditor reconstructed both cases and returned `PASS_RAW_AUDIT` with no errors. The OrbStack construction gate passed 8/8; candidate and auditor each ran once, with no retries.

The complete H/T/D/C/U, container conditions, evidence integrity discrepancy, and scope limitations are documented in [README.md](README.md). Exact commands, source identities, raw hashes, and stdout are in [RUN.json](RUN.json) and `results/formal-01/`.

This is a finite authored method result only. It does not establish a universal GUI or model-call lower bound, truthful live receipts, latency/cost, live task effect, or production safety. Historical predecessor outputs remain unchanged; four of their published checksum entries fail against the currently committed raw bytes and were not used as inputs here.
