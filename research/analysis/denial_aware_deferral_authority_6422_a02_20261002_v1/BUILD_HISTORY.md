# Build and test history

1. Wrote contract tests first. Initial red run: candidate source/fixture were absent; both expected contract assertions failed to execute, confirming the harness detects missing implementation.
2. Added candidate and raw-only auditor. The next red run exposed an incorrect test expectation (three, not two, valid-looking but unauthorized baseline reopens) and positive fixture evidence that omitted the frozen evidence-kind field.
3. Corrected the expectation and fixture; added evidence-kind equality to both candidate and independent oracle. A subsequent red run correctly rejected the still-incomplete fixture. Added the required evidence-kind to positive/valid-looking rows.
4. Green host construction suite: 3 tests passed. This is test evidence, not the formal candidate/auditor invocation.
5. Formal candidate invocation: one, exit 0, output `candidate_output.json`.
6. Separate raw-only auditor invocation: one, exit 0, status `PASS_METHOD_SCOPED`, output `audit_report.json`.
7. Formal retries: 0. Existing A01 files and outputs were not modified.

Audit-output note: the frozen audit source emitted the metadata scope string “six authored synthetic ... cases” although it reconstructed eight rows. Counts, fixture/raw hashes, decisions and five corruption results are internally recorded; the free-text scope is a retained reporting defect, explicitly disclosed in `REPORT.md` and not edited after the formal invocation.
