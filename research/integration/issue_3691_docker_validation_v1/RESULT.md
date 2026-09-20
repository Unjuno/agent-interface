# Issue #3691 Docker validation result

Date: 2026-09-21 Asia/Tokyo

## H/T/D/C/U

- **H:** The #3691 replacement auditor rejects predecessor raw/freeze substitution, the coordinated raw+freeze+replacement-study attack when checked against an external study digest, bool-as-int counts, and the retained event mutations in an isolated Linux container.
- **T:** At exact source commit `f823cbc77e87d2f9ff3456ddf49f2f819bbc340a`, run the frozen unittest suite once in a network-disabled, read-only-source container; then invoke the CLI in a separate fresh container on the committed raw/freeze/study bytes and retain its output.
- **D:** Container suite `PASS`, 8/8 tests. Separate-container CLI `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`, all 12 corruption controls true. The output includes the independently pinned replacement-study-manifest control. Test transcript and CLI JSON are retained alongside this report.
- **C:** OrbStack Docker Engine 29.4.0, Linux/arm64, Python 3.12 slim image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--network none`, `--read-only`, source mounted `:ro`, output isolated. The test container and CLI container were separate one-shot containers. No X11, GUI, input, model, or network activity; no predecessor formal allocation rerun.
- **U:** This validates only the finite committed mutation suite and CLI gate on Linux/arm64. It does not establish arbitrary audit completeness, native x86_64 behavior, or any XRes/runtime/product claim.

## Evidence drift found

The current committed `FREEZE.json` says native construction was 8/8 and names the replacement-study-manifest attack, but the committed `artifacts/native_tests.txt` reports 7/7 and `artifacts/native_audit.json` has only 11 controls. The Docker suite independently ran 8/8 and the separate CLI emitted the twelfth `replacement_study_manifest: true` control. The old native artifacts were not changed; this discrepancy is preserved here rather than silently backfilled or treated as byte-identical reproduction.

## Decision

`PASS_DOCKER_VALIDATION_WITH_PRIOR_ARTIFACT_DRIFT`. The required isolated tests and fresh-container CLI gate passed on the frozen source. The discrepancy is an evidence-packaging defect in the predecessor construction record, not a failed Docker gate. Keep the original artifacts immutable and review this result before closing #3691.
