# #4295 audit-control-only successor — 2026-10-01

Allocation: `specialist-regeneration-4295-controls-20261001-01`

Frozen current main: `f346b787a5a31381f51c0b7bd19740c3c7380db7`

This is a separate, one-shot audit-control experiment after the predecessor
formal allocation STOPped on a command-argument deviation. It does not rerun
the candidate or rewrite/relabel that STOP. Its only subject is whether the
preserved frozen auditor rejects its twelve preregistered corruptions when the
control harness is invoked with the correct auditor-script argument.

## H — hypothesis

The preserved raw-only auditor rejects at least 10 of the 12 frozen semantic
and provenance mutations when `controls.py` receives the actual `audit.py`
program path rather than an audit-result JSON path.

## T — one-shot control-only experiment

- Frozen input raw: `specialist_regeneration_4295_formal_20261001_01/results/formal/FORMAL_RAW.json`, SHA-256
  `8fe7767b456cc5ca70285b426c492675952c3247f55400d71233aa9780412d3e`.
- Frozen clean audit result SHA-256:
  `0dd886dd70f6e86622ba74a6aa98b4d3faf94b2e394816c6a41eb51316869b34`.
- Use the preserved `controls.py` and `audit.py` source members unchanged,
  after SHA manifest verification.
- Execute exactly once:
  `python3 -B <source>/controls.py <raw> <source>/audit.py <new-output>`.
- Candidate invocations = 0. No new formal rows, candidate rerun, threshold
  tuning, or output replacement. The failed predecessor `CONTROLS.json` stays
  untouched.

## D — decision

`PASS_AUDIT_CONTROLS_SUPPLEMENTAL` requires control process exit 0, all 12
mutations enumerated once, at least 10 rejected, and unchanged input/source
hashes. Fewer rejections = `FAIL_AUDIT_CONTROLS_SUPPLEMENTAL`; source, receipt,
or command ambiguity = STOP. This result can supplement the predecessor's
candidate evidence, but cannot by itself relabel its
`STOP_PROTOCOL_DEVIATION` or satisfy the Issue's scientific hypothesis.

## C / U

This tests only the frozen auditor's specified mutation set on one retained
synthetic raw. It is same-author process separation, not external review. It
does not establish specialist quality, generalization, latency, task value, or
production readiness.
