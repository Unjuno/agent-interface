# Scorer/event join: corrected construction entry points

Use `file_join.py --run-dir` for the complete source-checked bundle consumer.
It composes A02's artifact, event-transition, exact-JSON-type and source-byte
validation with the corrected classifier from
[missed_admission_guard_v1](missed_admission_guard_v1/README.md).
See [the composition repair](FILE_JOIN_CONSUMER_ROUTE_REPAIR.md) for exact
source identities and ordinary unit verification. This is a source repair,
not a new formal experiment or a live-runtime result.

- Direct function: `missed_admission_guard_v1/candidate_v2.py::classify_intent`
- Separate JSONL files: `missed_admission_guard_v1/file_join_v2.py`
- Complete source-checked directory: `file_join.py --run-dir`
- Historical metadata-policy directory wrapper:
  `missed_admission_guard_v1/runtime_bundle_v2.py`

The historical `candidate.py` remains byte-identical and has a known boundary
defect: a scorer row exactly at first input is skipped before its missed-period
flag is checked, so a later gain can be accepted despite that missed period.
Do not select that historical classifier for new classification work.
The shared `file_join.py` has evolved in A02 and now explicitly imports the
corrected classifier for both of its helpers. Its prior bytes remain in Git
history. `runtime_bundle_a01_20261005/runtime_bundle.py` remains byte-identical,
but its imported file consumer now uses the corrected classifier; that wrapper
still performs only its documented historical metadata checks.
Retained PASS records cover their original tested cases and do not establish
that the newly tested boundary was correct.

The correction rejects that missed period while keeping the same freshest
pre-input baseline, bounded post-input observation, and rejection semantics.
The original raw results, reports, freezes, and historical manifests are
preserved. Current composition manifests fingerprint the changed import,
new tests and documentation; they do not retroactively alter original results.
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
