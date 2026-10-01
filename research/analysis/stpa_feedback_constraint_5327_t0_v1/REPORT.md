# STPA-derived feedback constraint — Issue #5327 T0

The first allocation stopped before container start because the host bind source was missing. The second runner produced a scoped synthetic PASS, but its independent oracle correctly returned STOP after exposing a sequence/ack semantic mismatch. A separately frozen third allocation corrected the oracle distinction; Docker runner and independent audit both pass for 20 synthetic policy/scenario traces.

The fixture demonstrates that an exact-sequence feedback monitor blocks two deliberately modeled missing/stale-verifier-feedback admissions while preserving a current acknowledged PASS. Local gates and a documentation-only STPA mapping admit those synthetic traces. A separate fail-closed-unmapped policy rejects the unmapped action. See [`results/formal-03/RESULT.md`](results/formal-03/RESULT.md), `FREEZE*.json`, and `results/formal-01/STOP.json` / `results/formal-02/AUDIT_STOP.json` for full evidence.

This is one analyst-specified synthetic causal scenario, not an exhaustive STPA analysis, runtime implementation, empirical hazard finding, or safety proof. Real topology, feedback semantics, and mapping completeness remain unverified.
