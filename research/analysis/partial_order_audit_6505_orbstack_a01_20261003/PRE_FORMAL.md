# Pre-formal record

- Intake/base: `f8e71fc777100281c67a51233b222334fada2863` (current main at freeze).
- Open Issue #6505 had no formal successor allocation, open PR, or matching research branch at the ownership check. PR #5393 and #4914 are merged; #4914 is only the already-preserved two-event mutation-selection probe.
- OrbStack context: `orbstack`; Docker Engine 29.4.0, server platform linux/arm64, cgroup v2. The only running shared container observed was `unjuno-native-ci-6092`; it is unrelated and was not modified. No other active #4889/#6505 audit container was present.
- Pinned Python image was already cached as `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, platform linux/arm64; no pull is allowed or needed.
- Host construction tests passed 7/7; the full local analysis-index workflow passed 18 commands / 111 tests; syntax compilation passed. The latest-main index has 550 retained directories. Full input reconstruction and the 11,111-row independent audit remain reserved for the one formal audit-only invocation.
- Original candidate invocations by this successor: 0. Original auditor invocations by this successor: 0. Successor formal invocations: 0 at this pre-formal record. Retries: 0.
