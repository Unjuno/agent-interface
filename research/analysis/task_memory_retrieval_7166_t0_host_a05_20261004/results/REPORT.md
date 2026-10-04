# A05 result — PASS_METHOD_SCOPED

The frozen candidate ran once, exited 0, and emitted 72 rows. The independent
raw-only auditor ran once, exited 0, and reconstructed the base result as PASS.
All six mutations changed raw row content and were rejected: wrong label,
source hash tamper, ambiguous identity pick, authority escalation, dropped
history event, and forked-lineage pick. Allocation disposition:
`PASS_METHOD_SCOPED`.

This directly addresses A03's retained `FAIL_METHOD`, where the frozen
wrong-label mutation was a no-op (NONE changed to NONE). It also follows A04's
pre-candidate stale-main STOP without modifying that predecessor. A05 does not
prove a benefit of task-conditioned retrieval; it verifies only the finite,
authored label/provenance/abstention/no-authority fixture and effective
mutation-auditor contract.

Formal candidate/auditor invocations are 1/1, retries 0. Exact stdout, JSON
outputs, hashes, freeze, and scope are retained in this directory. No model,
GUI, natural retrieval backend, token/image cost, task effect, latency, runtime
or product evidence was collected.
