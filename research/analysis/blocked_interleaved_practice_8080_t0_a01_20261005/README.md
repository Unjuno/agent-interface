# Issue #8080 T0 A01 — blocked vs interleaved practice

This no-participant package checks whether the planned schedule contrast is
constructible with the same procedure variants, attempt counts, materials, and
feedback in both arms. It does not test learning, delayed retention, transfer,
or live GUI behavior. Issue #8084's separate adaptive-vs-random T0 is not reused
or changed.

The only procedure effects are reversible in-memory flags. The candidate
receives `design.json`; held-out IDs and effect truth are in the separate
`scorer_fixture.json` used by the auditor. This is a local method fixture, not a
security boundary against code that could read the whole checkout.

See [PROTOCOL.md](PROTOCOL.md) and [REPORT.md](REPORT.md) for H/T/D/C/U,
reproduction, result scope, hashes, and the container-runtime disposition.
