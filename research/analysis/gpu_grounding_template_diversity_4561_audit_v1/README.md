# Issue #4768: independent #4561 result audit supplement

This additive audit-only package independently validates the retained #4561 raw predictions against its frozen corpus manifest. It does not change, replace, or rerun the original allocation.

## Result

- Input SHA-256 pins matched: raw result `5ff992341e4f28357a4b0bdd1166d7c2a33e1aadab80fd8b576500c3a3b9fe97`; corpus manifest `7e4958551a229d75ba8da8fe23fb47b7c013d3228a7c6aabf745848b5004c9f7`.
- All 96 seed x arm x held-out-image rows matched the frozen image/family/target-cell/target-point mapping; no missing, extra, duplicate, or unknown case.
- Independent metrics reproduce the original scientific HOLD: narrow 12/48 (25.0%); broad 10/48 (20.8%); broad-minus-narrow -4.17 percentage points; all 96 rows yielded; accepted-wrong 0.
- Six standard-library tests pass, including self-consistent target tampering, seed/arm/image/label substitution, duplicate/missing rows, and confidence/acceptance mutation controls.
- No training, GPU/model invocation, network request, threshold change, or result tuning was performed by this supplement.

## Re-run

Fetch current main in a local Git repository, then run:

```powershell
python audit.py --repository C:\path\to\agent-interface --ref FETCH_HEAD
python -m unittest discover -s . -p test_audit.py -v
```

The auditor reads the pinned raw-result and manifest Git blobs via `git show`; it does not require a checkout of the historical result directory. This is useful because the old allocation contains literal backslash characters in some retained PNG Git paths, which ordinary Windows checkout rejects.

The result's scope remains synthetic-only. This audit supplement does not establish real-interface performance or runtime readiness.
