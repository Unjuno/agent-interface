# O3 relevant-region contract scope

This additive contract is a finite fail-open evaluator. It admits a region only when
the observation and intent are current, the requested region matches, coverage is
complete, freshness and effect binding are explicit, ambiguity is absent, and no
authority grant is present.

It does not capture pixels, choose regions, send input, call a model, measure latency
or tokens, or establish integrated multi-application correctness. A passing unit
matrix is contract evidence only.
