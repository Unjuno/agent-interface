# Archival qualification: #5407 T2b host-construction package

This is an additive preservation note. The eight historical files are retained unchanged from [Draft PR #5727](https://github.com/Unjuno/agent-interface/pull/5727), source head `314fb76aaaa56fa46009e22146d227f1dd3f2771`, on `research/5407-capacity-aware-reallocation-t2b-current-main-20261001`. All eight Git blob identities also match closed-unmerged [PR #5723](https://github.com/Unjuno/agent-interface/pull/5723), source head `a0e6a71dd78a12a66537d02066f7000ffa4708cd`. #5727 remains the unmerged delivery successor; preservation must not close either research ownership or the source Draft, move its branch, or relabel the result.

## What exists and what is reported

The published package contains PREREGISTRATION.md, SOURCE_FREEZE.json, run.py, audit.py, and four files under results/host-construction-01/: raw.jsonl, AUDIT_RESULT.json, REPORT.md, and RESULT.json. The committed raw contains 50 nonempty JSON objects for workload seeds 0–49; its final extra CRLF blank line is retained.

REPORT.md and RESULT.json report `FAIL_HYPOTHESIS_SCARCITY_FIRST_WORSE_ON_FIXED_MATRIX`. Their historical independent-audit outcome is PASS. The reported safe admitted value is 1,794 for scarcity-first and 1,981 for value-first, with safe shortfall 2,251 vs 2,064 and cost 2,296 vs 1,970. Both constrained policies report zero unsafe admissions. These are historical recorded results, not an audit or experiment performed by this preservation work. No runner, auditor, unit test, simulator, or mutation control was executed for this archive.

The historical environment is CPython 3.11.9 on Windows host CPU. [Owner #5407 comment 5923934300](https://github.com/Unjuno/agent-interface/issues/5407#issuecomment-5923934300) preserves the host-only FAIL and audit-PASS report and explicitly leaves the separate network-disabled CPU-container reproduction unrun pending exclusive allocation. The owner remains open. This note does not authorize that reproduction or claim a container result.

## Exact committed bytes versus historical frozen-byte claims

All eight fetched byte sequences reproduce the source Git blob identities. Nevertheless, three committed byte sequences differ from their embedded historical SHA-256 claims:

| File | Actual committed bytes / SHA-256 | Historical claimed SHA-256 |
|---|---|---|
| run.py | 7,837 / `f1195e0c495cac6201ac5b55e8953be651062831039b1f4c98bf1b1b8ab9b4ce` | `39ed31072bc0734a6d7a5fc3de5d5a9bd8626ee6d2ca5d795ededfe1418a521d` |
| audit.py | 8,155 / `1d3c03e6bd97e551da1a0fffc1af13a2591196b3e02882d8b1e923ef6bf31828` | `b3a04fd65188a4a731056fddfb8b2c51709650256b78f79807a0b33e654c1d34` |
| results/host-construction-01/raw.jsonl | 391,637 / `5a35391504df0296ae0b41e793e28a6fc84dc1487f33c069aa667cd30872d4f0` | `402f53e118c3bf0dd92187eed5d4eb35476519dad4c4a622e26c77894a78e5fd` (claimed 391,635 bytes) |

For each file, a data-only in-memory hash of the bytes excluding exactly the final CRLF pair matches the historical claimed hash. This precisely explains the observed two-byte difference relative to those digests; it does not turn the committed bytes into the historically claimed bytes or establish what was executed. Originals were not trimmed, normalized, regenerated, or substituted. SOURCE_FREEZE.json's run.py and audit.py Git blob values match the committed blobs even though its SHA-256 values do not match their full committed byte sequences.

There is also a retained allocation-label spelling difference: PREREGISTRATION.md uses `issue5407-market-t2-capacity-reallocation-20261001-02`; SOURCE_FREEZE.json, RESULT.json and the owner comment use `issue5407-market-t2b-capacity-reallocation-20261001-02`. This archive records the difference and does not rewrite or infer an authenticated alias.

## Scope and ownership

Synthetic deterministic allocation construction only. The source excludes deadlines, task DAGs, strategic bidding, nonstationary costs, real agents, truthfulness, production and runtime claims. The historical FAIL is not promoted by retaining it. Owner [#5407](https://github.com/Unjuno/agent-interface/issues/5407), both historical source branches, and Draft #5727 are preserved. Any later source repair, reproducibility investigation, container run, or new allocation is separate work requiring its own authorization and evidence.
