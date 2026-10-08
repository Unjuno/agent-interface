# Query/retry linearization boundary

Issue: #4126  
Result: **PASS_QUERY_RETRY_LINEARIZATION_SCOPED**  
Publication: retrospective evidence publication; this was **not** publicly preregistered.

This directory publishes the completed 54-case local subprocess/SQLite study that tested whether a correct read-only `NOT_FOUND` status can safely authorize a later retry.

Key result:

| policy | cases | extra same-operation effects | changed-payload effects |
|---|---:|---:|---:|
| CACHE_QUERY | 18 | 8 | 2 |
| SPLIT_RECHECK | 18 | 6 | 2 |
| ATOMIC_DEDUP | 18 | 0 | 0 |

All three policies atomically commit the local counter effect and receipt. The only changed factor is where exact operation identity/content is checked. `ATOMIC_DEDUP` checks inside the same write transaction that applies the effect.

Evidence summary:
- 54/54 formal cases
- 108 worker exit receipts reconciled
- two outer batch exits = 0
- separate raw-only audit errors = 0
- 12/12 corruption controls rejected
- current-main-at-intake `runtime/cli_v1/attempt.py` vendored byte-identically, Git blob `bd1725a18b6aef6f45c62297cbd794c760ea0a9f`
- no model, GUI/input, external network, credentials or user data

Read `PLAN.md`, `REPORT.md`, `AUDIT.json`, and `CASE_SUMMARY.json`.

The review capsule is in `CAPSULE.b64`; decode with standard base64, then verify SHA-256 `f66860d2cc821550969e556bc158531f57e80cc71c5d85a38e3af303dc02fa2d`. It contains the exact readable source/audit/summary files listed in `CAPSULE_MANIFEST.md`. It intentionally excludes the large per-case SQLite/raw directory tree from GitHub publication in this PR. The separately retained full 531-member local ZIP is SHA-256 `18b157aaaaf1200f16b687c5029072f9d90823957187751d5e4a6040ef84f6df`; publication scope and scientific evidence completeness remain distinct.

Do not rerun the consumed formal allocation merely to obtain public preregistration. Any new experiment requires a new prospective scope and allocation identity.
