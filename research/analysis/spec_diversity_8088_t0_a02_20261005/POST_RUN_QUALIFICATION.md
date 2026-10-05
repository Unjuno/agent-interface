# A02 post-run qualification — C02 preservation-coverage HOLD

This qualification supersedes the preliminary `NO_INCREMENTAL_VALUE_SCOPED` result. The candidate and raw-only auditor incorrectly tested C02's pre-existing-state preservation by concatenating Work and Archive records after removing the new item, then comparing that flattened sequence with Work followed by Archive from the initial state. That comparison does not bind records to their source lists: moving an existing Archive item to Work can leave the concatenated sequence identical and pass the predicate despite violating “do not change any pre-existing item or list.” The auditor repeats the same gap.

The formal raw contains no such cross-list move, so its passing C02 row does not demonstrate complete C02 preservation coverage. Candidate/auditor outputs and invocations remain unchanged (1/1, retries 0); the 8/8 claim and study-level `NO_INCREMENTAL_VALUE_SCOPED` disposition are withdrawn.

## Disposition and successor gate

- A02 status: `HOLD_C02_LIST_IDENTITY_COVERAGE`; no study-level D decision.
- Do not rerun A02. Preserve the one-shot output hashes and this qualification.
- A03 must compare Work and Archive independently and include a control that moves a pre-existing Archive row into Work while still adding the requested Pack kit correctly. It must fail only the pre-existing-list-preservation clause.
- This is a bounded harness defect in a synthetic packet, not evidence of production or existing repository defects.
