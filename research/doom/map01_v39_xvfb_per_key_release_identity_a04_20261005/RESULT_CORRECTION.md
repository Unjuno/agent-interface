# A04 raw outcome and classification correction

The one A04 candidate outcome is `results/A04/RAW.json`: it generated one V39 admission and one matching per-key XSync release receipt, then timed out waiting for the first client-dispatched key event. It retained one non-key `MappingNotify`, no key edges, and Xvfb exit 0. The partial release receipt shows `owner_thread_keyup_verified: true`, `release_batch_complete: true`, and `owner_sample_ordered_after_batch: true`; the missing client edge means the planned 80-edge test is incomplete.

Auditor v1 treats every incomplete run as `FAIL`, contrary to preregistered STOP for timeout/incomplete trace. `SOURCE/audit_v2.py` corrects only this rule and records partial receipts, raw hash, and cleanup. `AUDIT_CORRECTION.json` binds v2 to the unchanged freeze and raw file; the candidate will not be rerun. Result: `STOP`, not a completed source/edge mismatch.
