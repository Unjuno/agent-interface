# Construction history

Before the formal freeze, construction tests found and repaired:

1. Preferences referring to a revoked/ineligible route were initially sent to the completion enumerator. The eligibility filter now removes such route pairs before ranking, as required by the Issue's authorization-first contract.
2. The candidate's strict-witness predicate initially required all principals to be strict; Pareto dominance requires every principal weakly prefer and at least one principal strictly prefer. It now requires a fixed principal to be strict across every valid completion.
3. The first independent auditor draft had a variable-name error in the same predicate. The independent construction oracle caught it; its implementation now uses rank-vector enumeration, separate from the candidate's ordered-partition recursion.
4. The requester partial profile has three, not two, valid weak-order completions: review > conflict, conflict > review, and review = conflict. The fixture and gate preserve all three.

These were pre-allocation construction failures. No formal candidate or auditor invocation occurred during these repairs.

When the report was added, the generated Analysis Index correctly flagged the new result directory as missing. The prescribed --write refresh added its entry; the subsequent exact index check passed with 368 retained result/failure directories.
