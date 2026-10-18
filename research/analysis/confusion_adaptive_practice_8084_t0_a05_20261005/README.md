# Issue #8084 A05 — diagnostic-reliability independent revalidation

**Outcome:** `METHOD_PASS_SCOPED`; diagnostic screen `DOES_NOT_SUPPORT_CURRENT_GATE_AS_RELIABLE_AT_N_GE_20`. Fresh allocation after A04's `HOLD_METHOD_GATE` (the duplicate-row mutation survived). A05 used 1,000 replicates per authored stratum/sample-size cell (12,000 rows) and a disjoint deterministic seed family. It corrected the auditor's pre-map row-cardinality check and kept the A02 gate unchanged. Candidate/auditor each ran once; exact commands, outputs and hashes are retained. At n=20, low-dispersion false activation was 376/1,000 (0.376, versus the frozen ≤0.05 criterion); at n=100 it was 47/1,000 (0.047). See [RESULT.md](RESULT.md).

Frozen H/T/D/C/U and execution controls are in [PROTOCOL.md](PROTOCOL.md). Candidate saw only observed diagnostic counts. The independent auditor got latent rates and exact raw candidate output. A03 STOP and A04 HOLD remain unchanged.
