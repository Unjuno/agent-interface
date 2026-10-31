# T0 A01 result — Issue #8624

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate ran once and exited 0. The independent raw-only auditor then ran once and returned `PASS_METHOD_SCOPED`, 123/123 checks, zero failures. It independently evaluated 1,312 Boolean worlds across nine fixed cases; it imports no candidate code. Both one-shot invocation logs, exit codes, raw output, audit, freeze and checksums are retained in this directory.

The finite discriminator behaved as preregistered:

- The monotone positive control produced a minimal positive match support equal to its five present prerequisites.
- For the paired exception fixtures, the positive eligibility support was identical (`candidate`, `covered`, `enabled`, `scope_ok`, `visible`), while the endpoint changed from `MATCH` to `NO_MATCH`. The positive-only query support was empty for the negative result.
- The absent `candidate=false` fact and present `modal=true` exception were each identified as direct causes with minimum contingency 0.
- In the contingency fixture, the present `exception=true` fact was a cause only after toggling both prerequisites; its minimum contingency was 2 and its declared responsibility was 1/3. The global robustness radius was 1 because `quick_path=true` alone flips the result. The minimum flip set (`quick_path`) therefore differs from the designated per-fact contingency.
- The ten-variable dense fixture exceeded the 512-world budget and returned `UNKNOWN_TOO_LARGE` without a partial explanation. The incomplete-scope fixture returned `UNKNOWN`, not `NO_MATCH`.

Construction checks passed 8/8 in normal and optimized Python. They exercised fact-polarity change, intervention-domain expansion, a same-stratum dependency, endpoint mutation and omitted mutable-fact rejection. These are construction checks, separate from the one candidate and one auditor invocation.

This result validates only the declared finite Boolean rule model and its intervention semantics. It does not establish completeness of any GUI candidate universe, correctness of observed absence, real-world causal relevance, action safety, rescan value, latency, cost, or user benefit. It changes no runtime behavior and does not replace #5865's query-completeness gate.
