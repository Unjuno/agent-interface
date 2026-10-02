# Formal allocation 02 (T0b)

This directory holds the fresh formal execution for Issue #6519 allocation `AFFORDANCE-REGRESSION-6519-T0B-20261002-01`. See `PREREGISTRATION.md` for the immutable execution contract and `runner.ps1` for absolute-path-checked native WSLc invocations.

The earlier allocation 01 STOP is retained at `../formal_01_20261002/`; it is not overwritten or retried. T0b changes the runner only, uses separate outputs, and reuses the exact frozen candidate, fixture, and independent auditor. Formal runs are staged: construction first; candidate only after construction passes; auditor only after candidate output is retained and copied byte-for-byte.
