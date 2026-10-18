# Issue #6600 fixed-dose practice-order ledger T0 A01

## Result

`PASS_METHOD_SCOPED`. After preregistration comment [#6600](https://github.com/Unjuno/agent-interface/issues/6600#issuecomment-6051375777), the frozen candidate ran once and emitted two arms / 12 rows (exit 0). The separate independent auditor ran once (exit 0): six task slots per arm, no errors, six of six mutation controls rejected, exact effect-truth labels preserved, equal assessment history, and zero candidate actions, task effects, or participants.

The verified property is schedule-ledger integrity for the authored finite fixture. Blocked order is `A1,A2,B1,B2,C1,C2`; mixed order is `A1,B1,C1,A2,B2,C2`. The arms share the same task multiset and task-level facts/support/stop/skip conditions. No direction-of-benefit prediction was tested.

## Evidence and reproduction

- Source freeze and hashes: [`FREEZE.json`](FREEZE.json); preregistered source commit `19eacd91e3d42c766d6282b777c47c6067f043ff`; base main `d4eaac02eced2e6ebf2e8d29642343048661d71b`.
- Raw candidate output SHA-256: `f56ed0efef12fddc3b3ee8cc257847d31a7bce90cc8882220a428a9995988bca`.
- Independent audit output SHA-256: `e62e0b60f2cddcaa650860bc43779539c17c71c513a3db6a4a8e7936d0157076`.
- Construction tests: 9/9 passed; Python compilation and `git diff --check` passed before formal invocation.
- Formal candidate and auditor invocation counts: 1 each; retries: 0.
- Runtime: Python 3.14.5, Darwin 27.0.0 arm64; standard library only.
- Docker was not used. Intake observed Docker content-store inspection failure; this deterministic, non-effectful T0 did not require a container, and the host-only execution is explicitly scoped as such.

Exact invocation commands are in the Issue preregistration comment and [`PROTOCOL.md`](PROTOCOL.md). The audit output and all source/oracle files are retained beside this report.

## Scope and next gate

No participants, human allocation, GUI, model, network, task action, or learning endpoint were involved. This does not show that mixed or blocked practice improves acquisition, retention, transfer, task safety, or user benefit. A human T1 remains unauthorized and requires its own reviewed protocol, consent/safety/accessibility/privacy review, and independent allocation. The older #6730 result and assessment-history evidence are unchanged.
