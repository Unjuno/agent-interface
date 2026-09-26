# Provenance clarification

The formal result's embedded `allocation` field is `needle-role-graph-3775-v1`, a stale literal copied from the source runner used to construct this compact successor. The actual preregistered allocation is `needle-role-graph-3779-compact-v1` tracked by Issue #3780 and branch `research/needle-role-graph-3780-compact-20260921`.

The exact executed runner bytes are identified by SHA-256 `b9f92af480255b11febc607feb527827334ffa2ec26b1881b1c2166afd3cd5b8`; the raw envelope and its uncompressed result digest are retained unchanged. Do not interpret the embedded string as a reference to unrelated issue/PR #3775.

This is a metadata/provenance defect, not a data-row transformation: the independent audit verifies all 12,288 packed role rows, their per-role aggregates and flat/graph identity, all graph-control records, snapshot results, and base immutability. No source, raw result, threshold, or decision gate was edited after the formal run. The report retains the scoped empirical PASS with this warning made explicit.
