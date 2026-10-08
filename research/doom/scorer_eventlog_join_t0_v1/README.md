# Scorer/event join: corrected construction entry points

Use [missed_admission_guard_v1](missed_admission_guard_v1/README.md) for the
corrected classifier and JSONL consumers. This is an ordinary unit-tested
source repair, not a new formal experiment or a live-runtime result.

- Direct function: `missed_admission_guard_v1/candidate_v2.py::classify_intent`
- Separate JSONL files: `missed_admission_guard_v1/file_join_v2.py`
- Co-located runtime directory: `missed_admission_guard_v1/runtime_bundle_v2.py`

The historical `candidate.py`, `file_join.py`, and
`runtime_bundle_a01_20261005/runtime_bundle.py` remain byte-identical for
reproduction. They have a known boundary defect: a scorer row exactly at
first input is skipped before its missed-period flag is checked, so a later
gain can be accepted despite that missed period. Their retained PASS records
cover only their original tested cases; they do not establish that the
boundary is correct. Do not select those historical entry points for new
classification work.

The correction rejects that missed period while keeping the same freshest
pre-input baseline, bounded post-input observation, and rejection semantics.
The original raw results, reports, freezes, and hash manifests are preserved.
The independent `saved_record_audit_v2` remains valid for its separate pinned
one-fixture history and is not evidence that every classifier boundary passed.

## Historical runtime-bundle reporting clarification

`runtime_bundle_a01_20261005/RAW.json` retains exactly seven cases: valid,
changed source hash, unexpected source entry, changed summary count, wrong
summary schema, controller-visible summary, and missing summary. Changed
frozen policy and malformed scorer rows are additional ordinary unit tests,
not two additional rows in those seven saved cases. The malformed-row unit
test detects the appended row through sample-count mismatch.

That package's `audit.py` independently checks saved decision/reason labels,
case completeness, scope fields, and the source-policy hash. It does not
independently recompute scorer history or prove the saved metadata mutations.
This is distinct from `saved_record_audit_v2`'s independent counter-history
reduction. See the corrected package README for exact verification commands
and counts rather than interpreting a combined test count as a full-repo run.

All results remain synthetic construction and saved-data validation. Neither
the correction nor the retained metadata checks establish live behavior,
episode co-origin, effect time, causation, recovery efficacy, or MAP01 completion.
The historical container STOP and separate live-allocation hold remain.
