# Preserved predecessor record

Four-route A02 is retained without modification in draft/published evidence PR #7919: https://github.com/Unjuno/agent-interface/pull/7919 (observed head `b68685985152e0319cc29d7bc88b583f2c79a786`). Its candidate ran once and emitted 6,624 rows; its formal auditor failed at startup because the loaded oracle module lacked `__file__`. A separate read-only audit reconstructed all rows, found the candidate's context-insensitive preference-only cache reused baseline certificates for grant/protected controls, and reported zero safe-beneficial deviations under the selected utility. The candidate, raw output, failed audit, supplemental audit, and hashes remain in that PR.

A03 is a new allocation to validate the four-route control behavior with a full evaluation-input cache key and one working independent formal auditor. A03 does not alter A02's HOLD, claim that A02 passed its control gate, or treat the post-run read-only audit as formal confirmation.
