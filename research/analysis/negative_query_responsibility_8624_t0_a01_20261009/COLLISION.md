# Concurrent same-issue allocation notice

The current Issue #8624 comment history shows another worker froze and ran the same scientific question in allocations A01 and A02, with A02's reported disposition `PASS_METHOD_SCOPED` in PR #8739. This packet's A01 is therefore a concurrent duplicate of the same Issue hypothesis, not a distinct Issue-level research contribution.

Preserve this packet's freeze, raw candidate, auditor output, STOP/FAIL history from the other worker, and all hashes unchanged. Do not pool these results, count this as an independent replication, use it to strengthen the Issue-level conclusion, or retry either CLI. The scoped computations remain individually reproducible as recorded, but the work is superseded for Issue-level progress by the canonical A02 result in PR #8739. PR #8741 is being converted to draft and its description is corrected to make this collision explicit.
