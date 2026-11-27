# Issue #57 current-main Chromium / caller-v3 smoke R05

R03 completed the UI action and independent exact POST, but its frozen auditor
overrequired OCR after navigation. R04 stopped before input: source review found
the evidence collector read `changed` before assigning it, and its condition
manifest also named the previous token. R01-R04 artifacts and dispositions are
preserved unchanged. R05 fixes observation-record ordering, derives the token
in conditions from the actual fixture variable, and writes the full caller
result before any assertion. R05 uses a fresh token and one new raw directory.

## Question and scope

Does current adaptive caller v3 plus compiled-execution composition complete
one isolated headless Edge form Submit when the pre-action form token is
confirmed by Windows OCR, and a loopback HTTP server independently checks the
POST body?

This remains a one-case integration smoke. The form is prepopulated; one UI
Submit is the only dispatched action. The model adapter is an offline fixture.
No external provider, user desktop, shared allocation, Docker, WSLc or
non-loopback host is used.

## Frozen procedure and gate

- Verify clean Git state, exact repo root, source paths/hashes and fresh raw
  output path before starting Edge.
- Use one new headless Edge process, private profile, local HTTP form and token
  `t991025-3`.
- Require exact OCR on the pre-action `verify_value` observation and
  `submission_pixels_changed=true` on the final `submitted` observation.
- Retain every capture, OCR and predicate row, observer exception, full caller
  accounting/receipt, exact server POST and cleanup status before assertions.
- Run the independent saved-data auditor once. No retry/replacement or tuning.

Scoped `PASS` requires source and capture hash agreement, one accounted offline
caller attempt, exact pre-action OCR, changed final submission evidence, one
Submit, one exact POST, outer `TASK_SUCCEEDED`, a one-transition compiled
`TASK_SUCCEEDED` receipt with verified release, and successful owned-process
and profile cleanup. Missing evidence is `HOLD`; a complete task-effect or
release contradiction is `FAIL`.

No target-generation change, two-action input entry, external provider,
efficiency comparison, recovery rate, MAP01 result, or Research Preview
readiness is claimed. This cannot close #57.
