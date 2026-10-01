# Cross-seed role-skill robustness — Issue #4479

This successor tests the narrow but passing seed-3789/role-C result from #3890 across ten fresh, deterministic seeds. It retains the same synthetic three-role family, small model, training schedule, data-only artifact format, receipt-gated A→B→C graph and loader checks. Only seeds and allocation identity change.

- Public contract snapshot: `ISSUE_CONTRACT.md`
- H/T/D/C/U: `PREREGISTRATION.md`
- Source provenance and one-shot Docker plan: `FREEZE.json`
- Construction checks never train. Formal uses the cached CPU-only Docker image, no network, and one orchestrated pass over all seeds.

Scope is limited to this synthetic family and fixed fixture. No production model promotion, real skill transfer, application effect, signature/authenticity, or runtime authority is claimed.

