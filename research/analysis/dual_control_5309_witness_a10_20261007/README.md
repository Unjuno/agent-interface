# Issue #5309 A10 — non-isomorphic witness/cost method check

This is a distinct finite successor to A03/A08 and does not modify their outcomes or A09's terminal STOP. It uses three different directed transition structures and tests whether witness-aware action ranking is conditional on model correctness and a fixed preservation-cost budget. The exhaustive design contains 132 cases and 264 arm rows.

Formal disposition: `FAIL_AUDIT_VERDICT_COUNT_BUG`; a read-only v2 reconstruction of retained raw is recorded separately and does not change the frozen gate. See [REPORT.md](REPORT.md), [RUN_RECORD.md](RUN_RECORD.md), and [FREEZE.md](FREEZE.md). The execution is host Python because the present OrbStack Docker content store is unreadable; process/file separation is procedural only, not container isolation. Scope remains method-only.
