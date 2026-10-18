# Issue #8604 T0 A01 — inert handoff-card method audit

This package tests only whether a finite synthetic handoff-card set and factual comprehension key can be held invariant and independently audited while disposition counts vary. It uses no participants and does not test Hick–Hyman transfer, response time, choice overload, or human comprehension.

## Package contents

- `PROTOCOL.md` — frozen H/T/D/C/U and decision boundary.
- `candidate.py` — deterministic 8-family × 3-condition card generator.
- `auditor.py` — separate fixed-oracle exhaustive card/key audit.
- `test_audit.py` — construction and adversarial rejection tests.
- `cards.json` — exact frozen candidate-visible fixture.
- `FREEZE.json`, `SHA256SUMS` — source/input identity at formal freeze.
- `REPORT.md`, `RUN.json`, `OUTPUT_SHA256SUMS`, `raw/` — one-shot formal outcomes after freeze.

The mandatory Stop safely choice appears in every condition; C2/C3/C4 refer to 2/3/4 total explicitly available options. All are inert semantic descriptions and no option dispatches an action.
