# Source-time expiry across negative-evidence handoff

- **Status:** Finite logical-time method result passed; visual/query completeness remains outside scope.
- **Source:** Issue [#8466](https://github.com/Unjuno/agent-interface/issues/8466), successor to [#5865](https://github.com/Unjuno/agent-interface/issues/5865).
- **Idea:** Preserve a negative-evidence receipt's absolute source expiry across agent/cache handoffs so forwarding cannot renew stale evidence by resetting a receiver-relative TTL.
- **Outcome:** T0 `PASS_METHOD_SCOPED` on ten finite rows; candidate and independent auditor each ran once, and 6/6 mutations were rejected. At receiver time 16, source-bound expiry returned EXPIRED while a sliding-TTL control incorrectly returned NO_MATCH; a genuinely re-evaluated epoch/expiry was accepted. Invalid clock/epoch/query/scope/missing-expiry cases stayed UNKNOWN. No GUI coverage or action-authority result follows. Merged [PR #8474](https://github.com/Unjuno/agent-interface/pull/8474) preserves the result.
