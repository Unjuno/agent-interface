# Issue #8587 T0 A01 evidence package

`PASS_METHOD_SCOPED` on a finite authored client/toolkit/OS projection fixture. Start with [REPORT.md](REPORT.md), then inspect the frozen [protocol](PROTOCOL.md), [freeze](FREEZE.json), [raw candidate](results/candidate.raw.json), [independent audit](results/audit.raw.json), and [run record](RUN_RECORD.json). `fixture_builder.py`, `model.json`, and `oracle.json` retain the exact inputs; the candidate never reads the oracle.

Construction tests passed 6/6 under normal CPython and `python -O` before freeze. The one-shot formal candidate and auditor each exited 0; retries were zero. The checksum manifest verifies retained source, input, output, and report bytes.

The result is finite method evidence only. It does not qualify a real GUI event source, prove source completeness or independence, establish semantic effects, or grant action authority. See [Issue #8587](https://github.com/Unjuno/agent-interface/issues/8587).
