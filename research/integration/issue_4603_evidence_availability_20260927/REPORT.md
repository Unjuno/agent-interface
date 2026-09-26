# Issue #4603 — immutable 60-case evidence availability STOP

## H / T / D / C / U

**H.** The 60-case #4284 allocation recorded by PR #4293 can be independently reconciled from its immutable GitHub evidence without rerunning either historical allocation, while leaving the separately merged 24-row PR #4292 unchanged.

**T.** On 2026-09-27, GitHub MCP confirmed:
- PR #4292 is merged; its body states 24 lifecycle rows and raw SHA-256 `dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31`.
- PR #4293 is open, head `393c4115add5e602ed279388a93dad4094daa687`, base SHA `14cfdf1a5f31138b308f98fd0e80fa75e887e65d`, mergeable=false; its body states 60 cases / 462 rows and raw SHA-256 `711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9`.
- #4284's frozen PLAN at its evidence branch specifies 10 schedules × 3 policies × 2 repetitions = 60 cases. PR #4293's diff independently exposes FINAL_RESULT (60 cases/462 rows), formal RESULT (60/462), AUDIT (60, errors=[]), CONTROLS (13/13), FREEZE (10 schedules/3 policies/2 repetitions), and REPORT with matching identities.
- PR changed-file enumeration and GitHub PR patches are readable; GitHub Contents readback of the same evidence paths returned 404 for both `main` and the source branch. Thus the compressed evidence parts and frozen source capsule cannot currently be retrieved as whole file bytes through the available MCP surface. No lossless raw XZ decode or SHA-256 recomputation was possible.
- The 24-row and 60-case raw hashes differ. They remain distinct; this report does not choose an authoritative replacement.
- No formal runner or row generator was executed.

**D.** `STOP_SOURCE_UNAVAILABLE` for the exact immutable raw/source bundle: structured result metadata and patches corroborate the stated count and hashes but do not suffice to decode/recompute the raw artifact hashes or independently check every raw row. Do not treat this as `PASS_EVIDENCE_RECONCILED_60_CASE_DELIVERY`, and do not integrate or relabel the 60-case artifact from patch snippets alone.

**C.** Authority-neutral, read-only GitHub metadata/patch inspection only. Prior allocations, branches, PRs, raw bundles and outcomes were not changed. The independent confirmation is limited to freeze/result/audit summaries plus the visible four-part compressed-data patches. The source branch remains available and untouched.

**U.** Whether the exact EVIDENCE parts, source capsule, raw rows and frozen source files can be fetched via git clone/archive or a future authorized artifact endpoint; whether those bytes match all declared hashes and the 60/462 denominator; whether the original 24 and 60 row sets are distinct allocations or a publication/scope mismatch; and whether safe additive delivery can pass the current generated index/CI checks.

## Provenance

- Issue: #4603; parent reconciliation: #4284/#4293; regeneration question #4295 remains untested.
- Current main at branch creation: not independently exposed as a ref SHA by the available GitHub MCP tool in this check; PR #4602 has since merged at `d6dacd3507ea23a7c5aafe82788c0a9d8b452834`.
- New evidence-only branch: `research/issue4603-evidence-availability-20260927`.
- New additive path: `research/integration/issue_4603_evidence_availability_20260927/REPORT.md`.
- No model/provider/GUI/OS-input/runtime call; no credentials; no networked container operation.

## Evidence references

- PR #4292: merged 24-row result, raw SHA-256 `dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31`.
- PR #4293: unmerged 60-case result, raw SHA-256 `711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9`.
- #4284 latest reconciliation comment says no new run/replacement is requested.
- #4295 prior construction-02's generated 128 formal-shaped draft rows remain retired, not formal evidence.
