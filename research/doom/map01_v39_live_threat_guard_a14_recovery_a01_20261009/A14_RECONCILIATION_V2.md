# A14 post-hoc reconciliation v2

This is an additive clarification. It does not replace or revise the frozen A14 preregistration, initial `AUDIT.json`, `A14_RECOVERY_CENSORING.json`, `A14_RESULT.json`, or public result. The original `AUDIT.json` (`FAIL`) is SHA-256 `6dc3b232c8cfca0709c5337a8fd9d2fa609ccf985f2f83201ac4ece4e010a1bc`; `A14_RESULT.json` (`HOLD`) is `9620785873143629ee92b0f234cbbcafd56d302040ac1546a7470e9e3a0d3b7f`; and `A14_RECOVERY_CENSORING.json` (zero qualifying policy guards) is `4dae23f0c9b4cdbbc7b5ba82b5d2855e8944d441aaa002132db0dfdc184fd14f`. The original public result bytes remain SHA-256 `2c0064255ea5339c50ac3414c29f445b763bfc5480f6cbc17d10732f712e5ffe`; the original Markdown result remains SHA-256 `d57b7418e222bde8d34325b9edeefa26e8d54f02af17411e8695b200515ad837`.

The original `HOLD` is correct for its preregistered recovery question. The frozen predicate in `audit_recovery_censoring.py:is_hard_health_guard` accepts only a policy invalidation with `health:below_hard_minimum` or a health outcome marked `HARD_INVALIDATED` with reason `below_hard_minimum`. No such policy guard appears in the 12-decision report, so recovery following that trigger was not exposed. The preregistration bounds the recovery observation to two later decisions; it does not equate every action-validity rejection with that policy trigger.

The retained report separately contains two distinct action-validity max-decrease rejections. The independent reconciliation script recursively finds the repeated nested receipts and deduplicates by `contract.action_fingerprint`, rejecting inconsistent duplicates:

| Decision | Action fingerprint | Health at source → fresh check | Maximum allowed decrease | Outcome |
|---:|---|---:|---:|---|
| 1 | `3e7ad755fef23df987e5ebca06c57fc1caa2dba4cf3eb977d499900759e9eea4` | 97 → 85 | 10 | Revoked after executor acceptance; report records owner/server release verified |
| 2 | `5d4d49020001d415b73a350efc051ec8d408f405fdebc130b23411ae0ee2e3e8` | 85 → 70 | 8 | Rejected before executor admission |

These are distinct from the preregistered hard-minimum recovery trigger. They show two action decisions were invalidated at different lifecycle stages when fresh health exceeded each action's decrease bound. The 85→70 decline is also consistent with the aggregate episode minimum of 61; this addendum does not infer that health protection was generally effective or that those invalidations caused an outcome benefit.

The reconciliation reads only the retained local `episode/report.json`; the public artifact contains the two aggregate receipts and the SHA-256 of that local source report, not raw prompts, images, or protocol content. It does not rerun the game, modify frozen artifacts, alter the original disposition, or authorize a new allocation.
