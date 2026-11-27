# R05 result — FAIL_COMPILED_COMPLETION_PREDICATE

## Disposition

**FAIL; no runtime task success.** The normal-mode positive case minted the
V5 point-derived handles, passed caller and compiled admission checks, OCR
matched the exact input `t9910254`, and dispatched both CDP actions. The local
HTTP server independently recorded exactly one `/submit` with
`value=t9910254` (`exact: true`). However, the compiled completion predicate
searched OCR text for the spaced phrase `ai integrated saved`; Windows OCR
returned `AIINTEGRATEDSAVED`. The predicate therefore failed, and the runtime
correctly yielded `SAFE_YIELD/effect_failed`; the caller returned
`EXECUTION_INCOMPLETE`, with no outer task-effect receipt or score.

The HTTP side effect is evidence that the form accepted the value, but it does
not override the runtime's failed visual completion gate. R05 is not a product
task-success pass. The changed-generation case and `-O` run were not started
because the first case failed. No model/provider calls occurred.

## Cleanup

The run recorded a profile-lock cleanup error. A follow-up query found zero
Edge processes whose command line referenced the generated R05 profile, and
confirmed that the profile directory was already absent. See
[`raw/cleanup-audit.json`](raw/cleanup-audit.json). No unrelated Edge process
was targeted.

## Evidence and next step

- Frozen conditions and source hashes: [`raw/normal/conditions.json`](raw/normal/conditions.json).
- Runner output and exit: [`raw/normal.stdout.txt`](raw/normal.stdout.txt), [`raw/normal.exit.txt`](raw/normal.exit.txt).
- Browser screenshots, OCR, exact POST, receipts and failure: [`raw/normal/positive/`](raw/normal/positive/).
- R06 may normalize OCR whitespace/punctuation for the completion-banner
  predicate only. The exact task-token comparison and independent HTTP scorer
  must remain unchanged, and R05 evidence must remain immutable.

This remains a fixture-level headless Edge/CDP result. It does not establish
physical input release, provider cost, repeated reliability, Calc/MAP01
coverage, matched efficiency, or public runtime readiness.
