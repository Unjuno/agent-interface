# C07 — independent audit of saved C06 histories

**Disposition: PASS_METHOD_SCOPED.** This is a separate read-only audit allocation. C06 remains `FAIL_METHOD` because its original mutation-control harness raised an exception; C07 does not rewrite that result.

The frozen C07 auditor (SHA-256 `bd3013abcb0f2d5e1c67c7dee170f8162d0f2b921480613dd8b327512939d730`) was invoked exactly once against the 15 C06 raw shards. No candidate was executed. All shard SHA-256 digests, byte lengths, and row counts matched the C06 manifest before audit.

Results: 197,376/197,376 histories unique; all six regime/policy groups had exact unit mass; the exact known-propensity expectation matched the all-action oracle; all 768 greedy histories were unidentifiable; and all four malformed-input mutation controls were rejected. Detailed metrics are in `AUDIT.json`.

This supports only the stated finite-design mathematical method result. It does not show exploration improves real-agent behavior, establish sequential learning performance, or support GUI-safety or product claims.

The C06 root-level raw files were retained. Their byte-identical allocation-scoped copies and custody note were added separately on the C06 branch; no original was deleted or modified.