# Issue #8466 — Negative-evidence handoff expiry

Successor experiment to Issue #5865's negative-evidence delivery work. The question is whether forwarding a negative receipt can improperly renew its freshness window when receivers apply a sliding TTL instead of preserving the source-time expiry.

- Hypothesis, finite protocol, scope, and one-shot commands: [PREREGISTRATION.md](PREREGISTRATION.md)
- Frozen source/input/oracle identities: [FREEZE.json](FREEZE.json), [SHA256SUMS.txt](SHA256SUMS.txt)
- Outcome: [REPORT.md](REPORT.md)
- Invocation counts and raw/audit digests: [RUN_RECORD.json](RUN_RECORD.json)
- Unmodified candidate output: [formal_01/RAW.json](formal_01/RAW.json)
- Unmodified independent audit: [audit_01/AUDIT.json](audit_01/AUDIT.json)

The result is method-scoped synthetic logical-time evidence only; see the report for limits.
