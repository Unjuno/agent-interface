# Issue #8500 T0 A02 — common-check successor

This is a fresh allocation following A01's retained `PASS_METHOD_SCOPED` and its post-run identification caveat. A01's candidate and raw outputs remain unchanged. The A01 note found that only the structured-memory arm consumed the fresh relation/boundary checks, so the apparent advantage did not isolate memory content.

A02 gives every arm the same fresh relation-graph and evidence-current checks, the same candidate exposures and order, one lookup, one review slot, and a 64-word context. The treatment differs only in the review input: no prior memory, an untyped prose reminder, or a relation-keyed typed boundary question. Six changed-envelope controls test whether a prior rejection is reopened when its boundary no longer applies. The independent auditor checks common-check parity across arms and includes a mutation that grants one arm unique verifier access.

The candidate is a deterministic, hand-authored scorer. `truth.json` is auditor-only. The auditor imports no candidate code. This finite method test uses Python's standard library; no human reviewers, model, literature search, GUI, network, live input, or deployed memory are involved.

Formal commands are frozen in `FREEZE.json`; the candidate and auditor each run once, with no retry. Raw outputs, logs, exit receipts, and hashes are retained under `raw/first-outcome/`.

Any PASS establishes only that this authored scorer and fixture exhibit the preregistered contrast under the equal-check design. It would not establish real research-agent behavior, discovery yield, scientific validity, creativity, or product benefit.
