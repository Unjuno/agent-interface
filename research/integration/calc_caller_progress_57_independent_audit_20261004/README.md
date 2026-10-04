# Independent saved-artifact audit: #57 caller progress

Disposition: `PASS_REAUDIT_SCOPED` for the preserved allocation
`CALC-CALLER-PROGRESS-57-4D74-P01-20261004`.

The merged allocation report discloses that its saved-only auditor was written
by the experiment worker. This additive audit independently reads the frozen
plan, source files, both raw results, host receipts, and the two saved FODS
workbooks. It verifies all frozen source digests, the exact one-line caller
contrast, one native execute/verify per row, zero model calls, caller progress
values, native and cleanup release receipts, terminal event cardinality, and
the exact six populated Calc cells and formula directly from the OpenDocument
XML. It does not import or call the allocation's `saved_oracle.py`.

The independent audit agrees with the bounded reported contrast: both arms
saved A1=101, B1=103, and C1=10403 with the expected formula; both returned
`TASK_NOT_VERIFIED` after the deliberately unavailable verifier; the main
caller returned no `execution_progress`, while the one-line retention arm
returned `{"status":"completed"}`. Each row has one native attempt, zero
model calls, and verified neutral release.

The initial independent checker output is retained as
[`CHECKER-FAIL-01.json`](CHECKER-FAIL-01.json): it incorrectly expected the
recorded empty button count to be an array rather than numeric zero. After
correcting that checker-only representation mismatch, the unchanged evidence
passed as [`RESULT.json`](RESULT.json). No allocation input was repeated and no
source, raw result, or original report was changed.

Run from the repository root with a fresh output path:

```sh
python3 research/integration/calc_caller_progress_57_independent_audit_20261004/audit.py \
  --output /tmp/calc-caller-progress-57-reaudit.json
```

Auditor SHA-256: `5a71094054e26b365e1b411176e87f451411437bee08ab9f6bc74a624d8d9114`.

Scope remains narrow. The test deliberately injected verifier unavailability;
it does not establish natural effect-verifier behavior, current-target semantic
admission, recovery efficacy, caller efficiency, model cost, all-descendant
shutdown, or the full #57/#3311 acceptance path. The frozen experiment source
is `e963d2181657ecd98135fb4bc6e87223a39cd169`; this re-audit was performed on
current repository main `13cd5f3dcdf43bfc2c6153e489753dd9f1077861` without
replaying the original allocation.
