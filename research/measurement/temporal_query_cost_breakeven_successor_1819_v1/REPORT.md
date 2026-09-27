# Temporal query-cost break-even successor of #1819

This is a pure exact-arithmetic successor. It preserves #1819 and makes no model, GUI, network, or runtime claim.

The candidate enumerates all 12,341 denominator-40 prior vectors for RECENT/LONG/EVENT/REVERSAL. The independent auditor reconstructs the same simplex without importing candidate helpers, checks extrema, equal-prior thresholds, and corruption controls.

Run:

```text
python formal.py
python audit.py
```

Expected scoped result: PASS. The exact thresholds are 6 image-cost units for CLASS_ONLY vs UNIVERSAL_FIXED, 5/2 for CLASS_ANCHOR vs CLASS_ONLY, and 17/2 for CLASS_ANCHOR vs UNIVERSAL_FIXED.

The result does not establish token savings, latency, model quality, GUI correctness, or a runtime policy.
