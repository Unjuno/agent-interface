# Result: executable Python predicate read tracing

Issue: [#4766](https://github.com/Unjuno/agent-interface/issues/4766), successor to #4233's held executable boundary and complementary to #1756's analytical result.

## Outcome

**PASS_DYNAMIC_READSET_SCOPED** on the single frozen 8-state trace: 64 observations across two pure predicates and four cache policies. Dynamic nested-`Mapping` read tracing exactly matched full recomputation, with zero unsafe reuses and zero false invalidations. It produced four valid hits on unrelated changes and caught risk/target generation changes, including ABA restoration under a new generation. The deliberately incomplete static declaration had one unsafe reuse; static-all had nine false invalidations. The independent auditor reported no errors and rejected all 8/8 evidence mutations.

This establishes only the frozen toy trace and wrapped, pure Python predicates. It does **not** demonstrate arbitrary Python dependency discovery, concurrency safety, timing/performance benefit, production readiness, or promotion into the runtime.

## Method and provenance

The exact source, trace, environment, gates, and commands are in `FREEZE.json` and `PREREGISTRATION.md`; formal output is `raw.jsonl` and the independent raw-only audit is `audit.json`. The runner and auditor each ran exactly once in separate local Docker containers, using pinned image `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` (Python 3.12.14, linux/amd64), network disabled, one CPU, 512 MiB memory, read-only root/source, dropped capabilities, and bounded process/tmp resources. No GPU or external service was used.

Formal runner exit: 0; rows: 64. Independent audit exit: 0; result: `PASS_DYNAMIC_READSET_SCOPED`; errors: `[]`.

| Evidence | SHA-256 |
|---|---|
| `raw.jsonl` | `af9dace34a667a2e75c002c0848286801237de52e2c27b3f698fabb5010b565f` |
| `audit.json` | `05deb0f64e4a5638657dfe1029cd87a439c69f73f49280c6544b12f130c44cb0` |

Construction history is disclosed in the preregistration: two pre-freeze harness/auditor expectation failures were excluded; construction-03 passed 3/3 tests. There was no formal run before the freeze, no formal retry, replacement, or tuning.

## Interpretation

The result supports the narrow claim that a proxy can observe nested mapping reads for these pure predicates and use those reads as a dependency set under explicitly supplied per-path generations. Completeness depends on all relevant reads passing through the proxy and writers updating generations atomically. Direct `dict` base-class calls, globals, object attributes, I/O, reflection, mutation, and unwrapped values remain outside scope. This is evidence for a possible implementation rung, not a resolution of arbitrary dependency completeness in #4233.
