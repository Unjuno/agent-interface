# Source lineage and rescue qualification

This current-main archive carries the original retained-data availability audit from draft PR #8256 without rerunning its candidate or auditors.

- Original branch: `research/59-astra-guard-observation-audit-a01-20261007`
- Original head: `fc90f1a86048299b5919508d7cdc174813f1601a`
- Original base: `decc1896e3e85ab2fdbb7ec4678f958eb6561d0f`
- All ten original package files are carried byte-for-byte. The source `SHA256SUMS` inventory is verified; `FREEZE.json` input hashes are also checked against the retained main-branch Astra event/report files.
- The result remains `PASS_OBSERVABILITY_GAP_ONLY`: absence of runtime health/ammo samples and guard-invalidation outcomes in one historical run only. It does not answer whether current main reacts to live threat-linked HUD changes; that Issue #59 gate remains open.
- Rescue-local validation is archival integrity, JSON/AST syntax, and repository indexes only. It does not repeat the consumed candidate/auditor allocation or create new empirical evidence.
