# T1 A08 terminal STOP — false conflict and dropped prior claims (2026-10-08)

**Disposition: `STOP_FALSE_CONFLICT_AND_PRIOR_CLAIM_DROPS`; no cadence result.** Candidate was intentionally stopped after the prefix-4 consolidation emitted `conflict:exact_effect` for sources `src-01` and `src-03`, which represent different actions/contexts and are not a same-subject contradiction. The same output also dropped prior claims for episodes 1–3, retaining only new ep04 plus the false conflict. This violates the frozen transition contract. The candidate continued briefly after the stop signal arrived and preserved 67 rows total. Auditor was not invoked because the candidate was incomplete. No retry.

The A08 general kind mapping produced the allowed ep01 `verified_pattern`; however, general carry-forward and conflict-scope rules were insufficient. The next fresh allocation needs evidence-scoped identity/context for contradiction detection and a stronger no-loss transition contract.

- Candidate: one invocation, interrupted exit 130, 67 model calls; auditor 0; retries 0.
- Raw: 335139 bytes, SHA-256 `7a7feffb3b93b13b5b7cee6b70e8ee05fd2b8c40683b795f9e06a6f849a27618`.

Do not resume, score, or pool this allocation.
