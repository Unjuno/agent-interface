# Issue #3655 — committed evidence closure audit

This additive audit tests whether the merged #3642 evidence, exactly as stored in Git at the frozen main commit, reproduces its retained independent raw-only audit. It does not rerun GTK, XTest, MCP, model inference, or user-task input, and does not alter #3642's historical PASS.

## H/T/D/C/U

- **H:** The full #3642 `SHA256SUMS` inventory and its raw-only auditor can be reproduced from committed Git blobs alone. Missing or changed files must produce an explicit HOLD.
- **T:** At the frozen commit in `FREEZE.json`, enumerate the complete evidence subtree from the Git tree, hash each canonical Git blob against `evidence/SHA256SUMS`, materialize only committed evidence in a disposable local temporary directory, then invoke the exact committed `audit.py`. Preserve the inventory, auditor JSON, stdout/stderr, and exact source commit/hash.
- **D:** `PASS_COMMITTED_EVIDENCE_REPRODUCES` requires every listed artifact to exist and match and the committed auditor to return the retained scoped PASS. Missing files or hash differences yield `HOLD_COMMITTED_ARTIFACTS_INCOMPLETE`; retain exact auditor failures. Separately classify unavailable container execution as `STOP_CONTAINER_UNAVAILABLE`, not as a data-integrity result.
- **C:** Read-only Git-object analysis of merged #3642 only. No allocation, GUI process, input, model, or network experiment. Windows checkout line endings are excluded by reading blobs with `git show`.
- **U:** This does not revisit the original GUI result or establish product/runtime behavior. It only assesses committed-bundle reproducibility. No missing log is synthesized.

## Reproduce

Run from a checkout containing the frozen commit:

```powershell
python research/analysis/issue_3655_committed_evidence_audit_v1/audit_committed_bundle.py
```

The script uses Git objects as the canonical byte source, materializes the bundle in a temporary directory, and runs the predecessor's committed raw auditor there. It prints the full machine result to stdout and exits nonzero for the expected HOLD. `evidence/audit_result.json` is the retained human-reviewed summary from the same run, not a byte-for-byte capture of that stdout; compare its decision, missing paths, hashes, and nested auditor result rather than expecting identical JSON schemas.

## Result

At the frozen main commit, the committed tree omits two files required by both the manifest and auditor: `evidence/fixture.log` and `evidence/xvfb.log`. The remaining eight listed artifacts match their recorded SHA-256 values. The committed auditor therefore returns `HOLD_OR_FAIL`, naming exactly those two missing logs. This HOLD is independent of the container stop: Docker Desktop was unavailable, so this bounded local Git-object audit is not described as a container run.
