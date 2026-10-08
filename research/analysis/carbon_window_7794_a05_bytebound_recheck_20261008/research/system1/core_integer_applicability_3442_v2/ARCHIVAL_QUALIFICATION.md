# Issue #3442 v2 archival qualification

The 14 original files are preserved unchanged from source tip
`575f529aaac4ded60ec6158f291be7f96a8aa211` on
`research/core-integer-applicability-3442-v2-20261001`. This qualification and
the package `README.md` are additive.

The original formal `RESULT.md`, `PROCESS.json`, `audit.json`, and `raw.jsonl`
remain the authority for this one-shot allocation. Candidate exit=0 with 390
rows; frozen auditor exit=1 / `FAIL_OR_HOLD`; all 10 corruption controls
rejected. The identified defect is the frozen auditor's unconditional
operation-index expectation on accepted rows. Do not infer a runtime PASS or
FAIL, edit the original audit, or rerun candidate/auditor. A correction belongs
in a separately authorized successor and must not overwrite this record.

The preserved `LOCAL_CI.json` reports 8/8 preparation tests from before the
formal allocation and must not be presented as formal validation. In this
archive worktree, the isolated synthetic `test_auditor` suite passed 5/5; the
study suite was not run because this sparse checkout does not materialize its
`runtime/core_v1` dependency. No test read or audited `raw.jsonl`.
