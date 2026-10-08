# C07 — saved-data independent audit (2026-10-09)

## H — Hypothesis
Re-auditing C06's immutable enumerated histories with a corrected auditor will establish whether the finite exact-design identities and support checks hold. C06 remains FAIL_METHOD because its original auditor failed; this is a distinct saved-data audit, not a retroactive repair.

## T — Test
Read only the 15 C06 raw shards listed in RAW_MANIFEST.json, preserving their repository-root original paths as audit input keys. Verify SHA-256, byte counts, and row counts first. Run this frozen auditor once, without executing the C06 candidate or modifying raw data. Four malformed-input controls must all reject.

## D — Decision gates
PASS_METHOD_SCOPED only if all 197,376 unique histories reconstruct, six groups have exact unit mass, diagnostic known-propensity expectations equal their all-action oracle, all 768 greedy rows are unidentifiable, and 4/4 mutation controls reject. Otherwise record FAIL_METHOD or STOP with exact cause. Auditor SHA-256: bd3013abcb0f2d5e1c67c7dee170f8162d0f2b921480613dd8b327512939d730.

## C — Constraints
Exact Bernoulli finite-support design only; four trials/context; stated propensities and potential-outcome table. No sequential adaptation, empirical agent behavior, GUI safety, user outcomes, or product inference.

## U — Use
May support only the mathematical method claim for this finite design. It does not establish real-world exploration benefits or justify deployment decisions. No C06 source, result, or old data are altered.