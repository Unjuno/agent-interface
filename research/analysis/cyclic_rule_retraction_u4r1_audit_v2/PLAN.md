# Audit-only plan — Issue #4583

## Immutable input

Read the main-merged #4449 evidence at
`research/analysis/cyclic_rule_retraction_u4r1_v2/results/formal01/` without
copying over or modifying it. Pin Git blob IDs and SHA-256 digests for the
original freeze, sources, raw rows, conditions, input, process receipt, and
first audit report.

## Independent reconstruction

For each of the 64 six-rule masks and its no-change plus every active
single-rule deletion, enumerate all four interpretations of `{A,B}`. Intersect
the interpretations closed under the positive rules to obtain the least
grounded oracle. Independently derive the dependency cone, local-support
pruning state, and blind-invalidation state. Compare every field and order in
the 256-row raw corpus.

Compute both condition encodings independently: newline-delimited canonical
JSONL and escaped backslash-n separators. Verify which digest matches the
retained bytes and the original freeze. Do not edit the original freeze.

## Controls / run budget

First, construction-only self-tests use masks 1, 11, and 19 to validate the
auditor and its 10 targeted corruption mutations; they read no formal raw.
Freeze this auditor and inputs, push/read back its commit, then run exactly one
raw-only audit container. The only output mount is the successor's fresh
result directory. No original candidate invocation, formal rerun, retry,
replacement, or source repair is authorized.
