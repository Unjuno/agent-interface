# Current-main rescue re-audit (2026-10-07)

This record is additive. It does not change any historical candidate, auditor,
or STOP output. The checkout was `origin/main` at
`3dba6c86f212c37a2d80c844b816c38921a42cc5`.

## Retained-log checks

- `python3 research/doom/map01-v39-release-cleanup-overlap-v1/audit.py`:
  **FAIL 11/12**. The one failed check,
  `cleanup_case_exercises_execute_path`, looks for the historical
  `test_cleanup_inside_explicit_release_bracket_is_not_ordinary` test and its
  `owner.explicit_key_release_requests` assertion in the current-main test
  file. The retained candidate log contains the test; current main has since
  replaced that test source. The check does not invalidate the original saved
  log, but the old auditor cannot independently bind that log to its historical
  source from current main alone.
- `python3 research/doom/map01-v39-release-cleanup-overlap-v1/test_audit.py`:
  **PASS 5/5** mutation/consistency tests. No candidate was executed.
- `python3 research/doom/map01-v39-release-cleanup-followup-v1/audit.py`:
  **FAIL 13/14**. `all_adversarial_tests_present` checks for the three
  historical malformed-input test names in the current-main test file. They
  are absent there because that file has changed. Retained historical logs,
  exit receipts, recorded source-hash ancestry, and the remaining auditor
  checks pass.

The original source-bound auditor outputs remain the historical results:
12/12 for cleanup-overlap and 14/14 for the follow-up. The results above are
new current-main re-audit outcomes and are deliberately not presented as
passing audits. Source snapshots under `source/` pin the final #7395 head only;
they do not claim to represent every intermediate candidate. Further audit
improvement requires retaining each exact intermediate source tuple and
rechecking that tuple against the corresponding frozen manifests. Do not rerun
the consumed T0 allocation: its original STOP says one candidate invocation,
zero input/process starts, and no auditor invocation.

## Scope

These are consistency checks over saved logs and test-source identity. They do
not execute the old or current candidate, establish live X11 input/release,
application consumption, or promote the historical implementation into
current main. The old implementation/test PRs still need separate code review
and integration decisions; this package rescues only result artifacts.
