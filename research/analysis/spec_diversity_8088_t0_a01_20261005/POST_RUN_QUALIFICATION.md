# A01 post-run qualification — baseline oracle coverage HOLD

This qualification supersedes the preliminary `NO_INCREMENTAL_VALUE_SCOPED` conclusion in the original A01 report. The original candidate output, auditor output, source, and invocation counts remain unchanged and are preserved verbatim.

## Defect found in review

Contract C06 requires selecting Active to show all and only active Work items, and then selecting All to restore visibility of every Work item while leaving records unchanged. The candidate emits only one `visible` field (the Active result). Its `all_filter_restores_all` predicate compares IDs in the final stored Work records with IDs in the initial stored records; it does not observe the visible IDs after selecting All. Therefore it cannot detect an All-filter visibility defect. The raw-only auditor independently repeats this same semantic gap, so its 12/12 recomputation proves agreement on encoded predicates, not coverage of every explicit contract clause.

The formal raw has no All-view observation. The passing C06 row is not evidence that the All restoration requirement was tested. The original 8/8 baseline claim and `NO_INCREMENTAL_VALUE_SCOPED` disposition are withdrawn as unsupported. The four ordinary controls were still rejected as recorded, but they do not repair the C06 coverage defect.

## Disposition and custody

- A01 status: `HOLD_BASELINE_ORACLE_COVERAGE`; the study-level D decision is not reached.
- Candidate/auditor invocations remain 1/1, retries 0. No rerun or output replacement is authorized for this allocation.
- A02 must be a fresh allocation with explicit Active and All visible-ID snapshots, a mutation that leaves records intact but fails to restore All visibility, independent candidate/auditor predicates, and an independent check that each contract obligation maps to an observable raw field.
- This is a bounded harness defect in the synthetic study. It does not establish a defect in production software, any repository experiment, or the general value of specification-diverse challenges.

