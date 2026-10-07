# Construction/preflight record

The registered formal fixture candidate/auditor CLI counts remained 0/0 during
construction. Unit tests call the in-memory functions and are not counted as
formal fixture invocations.

- Candidate contract tests first failed against the placeholder implementation
  (4/4 failed as expected). Implemented all-offer denominators, no adapted-only
  estimand, deadline/generation checks, missing-evidence HOLD, and safety-first
  disposition. The subsequent contract suite passed.
- A later complete-fixture preflight initially returned `FAIL_AUDIT` with
  `SOURCE_GENERATION_MISMATCH`: the auditor treated the intentionally planted
  stale-cue negative as data corruption. The protocol requires this negative to
  be retained as `HOLD_MECHANISM_EVIDENCE`, while the same mutation in a benefit
  case must be rejected. The auditor was corrected to distinguish the frozen
  negative-control class from an unexplained mismatch.
- The complete fixture then reconstructed all 18 offers, nine pairs and eight
  case outcomes; the three planned auditor mutations (hidden offer, wrong
  generation in a benefit case, and altered release/effect receipt) were
  rejected by unit tests.

These were pre-freeze construction checks; no formal candidate or formal audit
was run at this stage. The initial bad preflight is not a scientific result.
