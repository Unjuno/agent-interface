# Issue #8635 T0 A01 — candidate CLI repair and held-out diagnostic successor

Fresh allocation following #8629's retained one-shot CLI failure. The original outcome remains unchanged. This package uses new held-out seeds (59, 71, 83, 97), the same finite six-stratum design, five deterministic policy profiles, and three arms (48 cases; 720 rows).

The successor adds end-to-end candidate and raw-only auditor CLI construction tests plus WSLc command and mount-staging contract tests. The candidate test reproduced the prior `NameError` before correction, then passed with 720 unique case-policy-arm rows after moving the CLI entrypoint below its helper definitions. Construction tests currently pass 21/21 in normal and optimized host CPython.

No formal candidate or auditor invocation has occurred for this allocation. The formal stage is pending the repository's shared WSLc coordination gate; this is not a scientific result. See [PLAN.md](PLAN.md) and [CONSTRUCTION.md](CONSTRUCTION.md).

Evidence remains synthetic method research only. It establishes no learned-agent, human, GUI, runtime-safety, latency, or product claim.
