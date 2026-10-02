# Formal failure — Issue #6615 T0B

Allocation: `ADOPTION-INCLUSIVE-CURVE-6615-T0B-20261002-01` (preregistration identity)  
Frozen base: `afea9a530cafd7af529df4c9e59f36b816bca24f`  
Environment: host-local CPython 3.14.5 on macOS.

## Observed execution

The corrected auditor passed its structural and semantic gates: 58/58 rows reconstructed, errors empty, learning fixture first comparable break-even at prefix 5, unsupported-host has no comparable prefix, setup-dominates has none through K=5, and failure/control counts matched. Candidate process exited 0 with 58 rows; auditor process exited 0.

However, candidate stdout embedded allocation `ADOPTION-INCLUSIVE-CURVE-6615-T0-20261002-01`, while the frozen preregistration and FREEZE identify T0B. The fixture was copied without changing this run-identity metadata. This leaves the formal output misattributed and violates the experiment identity gate.

## Decision

`FAIL_PROVENANCE_GATE`. Do not count T0B as a passed formal allocation despite its otherwise passing audit. Preserve all frozen source, raw output, stdout/stderr, audit and hashes unchanged. T0C adds an exact stdout/fixture/FREEZE allocation equality check and is recorded separately.

Artifacts in this directory: candidate stdout/stderr, raw event ledger, auditor stdout/stderr, audit JSON and FREEZE.json.
