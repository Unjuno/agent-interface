# Issue #5547 T0 — invariant-confluence boundary

This package retains one failed formal allocation and one corrected, finite successor. It tests only whether a small frozen state/join model exposes coordination-sensitive pairs. It is not runtime code and makes no distributed-systems or Agent Interface safety claim.

- Formal-01: `results/formal-01/` — raw candidate output retained; the later independent audit found the unlabelled integer quota merge was not idempotent. Disposition: FAIL.
- Formal-02: `results/formal-02/` — reservation identities are explicit set members. Candidate, independent raw-only oracle and five corruption controls pass. Disposition: scoped synthetic PASS.
- Earlier construction outputs and audit defects are preserved under `results/preflight*/`; they are not formal evidence.

The one-shot allocations have distinct IDs and output paths. Do not overwrite or rerun them. See [PLAN.md](PLAN.md), [formal-02 freeze](FREEZE-02.json), and the machine-readable reports under each results directory.
