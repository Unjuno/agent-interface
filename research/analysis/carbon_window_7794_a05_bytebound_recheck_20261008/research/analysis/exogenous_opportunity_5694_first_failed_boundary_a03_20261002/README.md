# #5694 A03 — first-failed-boundary attribution

This package preserves one preregistered native-Windows CPU candidate/auditor run. The raw-only audit replayed all nine rows and rejected all five corruptions (`PASS_METHOD_SCOPED`). The scientific hypothesis is **HOLD**: the `phase_hit` and `phase_miss` arms changed both capture schedule and observation horizon, so the planned phase-only contrast was not identified. No source, fixture, raw output, or result was repaired or rerun.

- [`PREREGISTRATION.md`](PREREGISTRATION.md): H/T/D/C/U and frozen method.
- [`FREEZE.json`](FREEZE.json), [`RUN_RECORD.json`](RUN_RECORD.json): allocation, commands, environment, and receipts.
- [`REPORT.md`](REPORT.md), [`ADJUDICATION.md`](ADJUDICATION.md): scoped audit outcome and hypothesis HOLD.
- [`execution/formal-01/`](execution/formal-01/): exact candidate raw, audit, stdout/stderr, and exit captures.
- [`SHA256SUMS`](SHA256SUMS): hashes for source, fixture, run records, and formal outputs.

The result is a synthetic method artifact only; it establishes no live-control, safety, human-tempo, or product claim. Prior #5694 A01/A02 artifacts are unchanged.
