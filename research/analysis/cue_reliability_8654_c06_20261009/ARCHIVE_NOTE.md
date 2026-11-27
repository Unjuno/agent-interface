# Issue #8654 C06 unique artifact archive

The 11 C06 source, freeze, report, and manifest files absent from merged C07
are copied byte-for-byte from branch `research/8654-c06-stochastic-support-20261009`
at exact tip `7f8bab0b6eece49bb5dfedb9598d3c48b30fb725`.

C06 remains `FAIL_METHOD`: its sole auditor invocation threw in the mutation
control harness. The separate C07 audit in merged PR #8671 does not rewrite
that first outcome. C06's 15 raw shards were not copied again because each
manifest SHA-256, byte count, and row count matches the corresponding shard
already retained under `research/analysis/cue_reliability_8654_c07_20261009/raw/`.

No candidate, auditor, or model was run while archiving these files.
