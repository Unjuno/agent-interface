# A06 retained first outcome

**Disposition: `STOP_A04_ARTIFACT_MANIFEST_KEYSET_MISMATCH`.** The one frozen audit-only process exited 1 while comparing artifact hash mappings. The bytes for `public.jsonl`, `oracle.jsonl`, and `candidate.jsonl` were hashed, but the code compared the three-entry A06 map for equality with A04's four-entry map, which also includes `first_audit`. It stopped before parsing JSONL or computing any score.

This is a harness/freeze comparison defect, not a TTC result. A06 scorer invocation count is 1; retries are 0. No candidate, generator, or previous auditor was invoked. Do not rerun A06 or amend this STOP. A02 remains `FAIL_METHOD` with its scientific comparison unscorable; A03 remains `STOP_AUDITOR_RUNTIME_ERROR`; A04 remains `PASS_RAW_RECONCILIATION_ONLY`; A05 remains `STOP_BEFORE_INPUT_READ_ARGUMENT_ROOT_MISMATCH`.

The exact command, interpreter, exit, stdout/stderr, freeze digest, and invocation counts are in `RUN_RECORD.json`. Construction tests passed 4/4 before the frozen invocation. No container or shared runtime was used.
