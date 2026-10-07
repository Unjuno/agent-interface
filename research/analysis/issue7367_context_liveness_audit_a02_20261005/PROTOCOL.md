# #7367 retained-workload byte-binding audit A02

## Scope and hypothesis

This is an audit-only successor to merged T0 A01. A01's candidate output, original audit, workload, and `PRE-RUN.json` remain unchanged. No candidate is replayed. A02 tests whether the retained A01 semantic PASS remains bound to the exact workload and raw bytes named by A01's pre-run manifest.

**H:** An auditor that checks only the raw output's workload hash against the workload currently on disk can accept a post-freeze workload mutation. Binding the workload bytes to `PRE-RUN.json` and the raw output bytes to a frozen SHA-256 should reject that mutation while allowing a fresh read-only semantic audit of the exact retained A01 bytes.

## Test and decision gate

Freeze copies of A01's `PRE-RUN.json`, `workload.json`, `run_a01.py`, `audit_a01.py`, `RAW.json`, and A01 `AUDIT.json`. Run the versioned v2 auditor once against the retained A01 raw output. The auditor verifies the actual workload digest against both `PRE-RUN.json` and the v2 freeze, verifies the raw output's declared workload digest, binds raw bytes to their frozen digest, verifies A01 source digests, and reconstructs A01's semantic checks from the preserved raw data.

The frozen mutation adds an 8,192-byte padding field to the declared-dead `stale-summary` record without changing the workload graph or liveness set. It updates the raw workload hash, changed record hash, and policy byte counts so the mutated raw is internally consistent with the mutated workload. Construction reproduction runs the original A01 auditor against that copy; it must accept the mutation. The v2 auditor must reject those mutated bytes against the original A01 freeze.

**D — `PASS_AUDIT_BINDING_REVALIDATED`** only if exact A01 workload/source/raw bytes match their frozen digests, the retained semantic audit reconstructs with all checks true, the mutation leaves the graph hash unchanged and is internally consistent, A01 v1 accepts the mutated copy, and v2 rejects its workload and raw bytes. Otherwise `FAIL_AUDIT_V2` or `STOP` with the first preserved evidence.

**C:** An external manifest could also bind the bundle, but A01 already placed the workload digest in `PRE-RUN.json`; the auditor simply did not enforce it. Recomputing the candidate is unnecessary for this provenance question and is expressly excluded.

**U:** This revalidation concerns only byte identity and semantic reconstruction of A01's finite synthetic output. It does not establish candidate correctness outside the frozen workload, open-world future-use completeness, model-context savings, tokenizer/runtime cost, model quality, GUI behavior, or product utility. SHA-256 integrity assumes the manifest itself is the trusted freeze anchor.

## Execution limits

Candidate invocations: 0. A02 v2 auditor formal invocation: 1, on the preserved A01 raw. No network, model, GUI, live task, or input action. The original A01 candidate and auditor counts remain unchanged.
