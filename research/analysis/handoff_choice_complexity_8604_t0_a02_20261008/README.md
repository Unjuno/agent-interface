# Issue #8604 T0 A02 — fresh synthetic card/key audit

Fresh successor to A01's preserved candidate CLI STOP. A02 tests the actual CLI output-custody contract and independently audits 24 synthetic cards plus their 120 factual comprehension-key entries. No user or participant study is involved.

## Files

- `PROTOCOL.md` — frozen H/T/D/C/U and allocation custody.
- `spec.json` — eight synthetic handoff facts; no hidden or personal data.
- `candidate.py` — CLI builds C2/C3/C4 cards and writes using exclusive-create.
- `auditor.py` — fixed-contract independent reconstruction; imports no candidate code.
- `test_*.py` — subprocess output/overwrite and semantic mutation tests.
- `FREEZE.json`, `SHA256SUMS` — frozen identity.
- `REPORT.md`, `RUN.json`, `OUTPUT_SHA256SUMS`, `raw/` — formal one-shot record.

No inference about humans, latency, choice overload, UI quality, or product behavior.
