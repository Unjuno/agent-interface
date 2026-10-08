# Strict runner-completion semantics — T6

T6 reproduced the preregistered defect in the frozen synthetic CLI auditor on Linux/amd64: candidate exits `[0,0,0,1,1,1,1,0]` and the independent raw-only auditor returned `PASS_INDEPENDENT_RAW_AUDIT` with no errors. This is scoped to the synthetic JSONL CLI boundary; it is not formal X11 or Issue #59 completion evidence.

See [RESULT.md](RESULT.md) for H/T/D/C/U, exact environment and outcome; [CI.md](CI.md) for local validation; and [FREEZE.json](FREEZE.json), `results/formal-t6-01/`, and `results/formal-t6-01-host/` for frozen identities and raw receipts.
