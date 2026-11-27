# Issue #57 current-main Chromium / caller-v3 smoke R06

R03 produced a successful scoped task outcome but its auditor overrequired
post-submit OCR. R04 stopped before input due an evidence-collector ordering
bug and carried a stale token in conditions. R05 completed successfully and
retained complete data, but both runs of its frozen auditor used an R04 literal
instead of the R05 task token. Preserve all prior outcomes. R06 fixes the
auditor to derive its expected exact POST from `conditions.json` and fixes the
task token at `t991025-4` before one fresh execution.

## Question and scope

Does current adaptive caller v3 plus compiled-execution composition complete
one isolated headless Edge form Submit when pre-action exact text is confirmed
by Windows OCR, and a loopback HTTP server independently checks the POST body?

This is one prepopulated-token Submit smoke, not a matched efficiency,
reliability, MAP01, provider, or V5 target-generation experiment. The model
adapter is an offline fixture. No external provider, user desktop, shared
allocation, Docker, WSLc, or non-loopback host is used.

## Frozen procedure and decision rule

- Verify clean Git state, root, source files/hashes, protocol/auditor paths and
  a fresh raw output path before Edge starts.
- Start one fresh headless Edge process with a private profile and a localhost
  form prefilled with exact token `t991025-4`.
- Require exact OCR in the pre-action `verify_value` observation and
  `submission_pixels_changed=true` in the final `submitted` observation.
- Preserve raw PNGs, each OCR/predicate/error row, full caller/model ledgers,
  compiled receipt, exact server POST, and cleanup status before assertions.
- Run the saved-data-only auditor normally and under `-O`. It derives the
  expected POST from the frozen conditions token; no literal is copied into
  the scorer. No retries, replacements, or tuning.

Scoped `PASS` requires matching source/capture hashes, one fully accounted
offline caller attempt, stage-specific visual predicates, exactly one Submit
and one exact POST for the frozen token, outer `TASK_SUCCEEDED`, compiled
`TASK_SUCCEEDED` with one completed transition and verified release, Edge
exit 0, and owned-profile cleanup. Missing evidence is `HOLD`; complete task
or release contradiction is `FAIL`.

No generation mutation, two-action input entry, external provider, matched
efficiency, recovery reliability, MAP01, or Research Preview readiness is
claimed. This cannot close #57.
