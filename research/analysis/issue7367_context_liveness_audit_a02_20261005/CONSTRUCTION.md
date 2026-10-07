# A02 construction receipt

The test first produced the expected RED: the retained A01 auditor returned
`passed=true` after an 8,192-byte payload was added to `stale-summary`, the raw
workload/record hashes were updated, and policy byte counts were recalculated.
The workload graph and liveness set were unchanged. This directly reproduces
the gap described in the Issue's post-merge audit note.

After adding the v2 input-binding check, the focused regression passed. It
confirms the original A01 bytes match `PRE-RUN.json`, the A01 auditor accepts the
self-consistent mutated copy, and the v2 checker rejects the changed workload
and raw bytes against the A01 freeze.

Pre-freeze construction commands:

- `python3 -m unittest -v research.analysis.issue7367_context_liveness_audit_a02_20261005.test_workload_binding` — 1/1 PASS.
- `python3 -m py_compile audit_a02.py test_workload_binding.py` — exit 0.
- JSON parsing for the copied A01 manifest/workload and `git diff --check` — exit 0.
- `construction_tests.py` creates a temporary hash manifest over the frozen inputs and executes the v2 audit-only path once as a construction check; the post-freeze formal invocation is a separate single container run.

The construction mutation and A01 v1 audit output are retained under
`construction_mutation/` and bound into the A02 freeze. No A01 candidate was
replayed and no original artifact was edited.
