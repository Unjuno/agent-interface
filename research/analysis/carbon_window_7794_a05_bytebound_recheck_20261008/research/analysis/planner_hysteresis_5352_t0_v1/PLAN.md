# Issue #5352 — deterministic hysteresis boundary rung

## Preregistration

- Base main: `14c1513c7ac516e5dc5b766b4fc99c1b8cbaa2ca`
- Allocation: `planner-hysteresis-5352-t0-20260930-01`
- Scope: one deterministic, model-free, local CPU exhaustive finite-trace rung. No random seed, model, GPU, CUDA, GUI, external tool, or network-dependent data.
- Execution route: host CPython only. Docker is withheld because #5085 reports an owner-unidentified running container and no explicit exclusive CPU-container lease. All source and outputs remain additive under this path.

### H/T/D/C/U

**H.** In short traces oscillating around an escalation boundary, fixed hysteresis or minimum dwell reduces mode transitions relative to an immediate single-threshold rule while preserving same-observation response to every critical or stale event. A stateful policy can reduce switching yet diverge from the raw reference's final mode; that is a gate failure, not something to tune away after seeing results.

**T.** Exhaustively enumerate every sequence of lengths 1–3 (8,420 traces total) over 20 typed symbols: risk in `{0.0, 0.3, 0.5, 0.7, 1.0}`, freshness `{fresh, stale}`, and critical flag `{off, on}`. Compare:
1. `raw`: escalate this row iff stale, critical, or risk >= 0.7.
2. `fixed_hysteresis`: enter at risk >= 0.7 or critical; exit from escalated only at fresh risk <= 0.3. A stale row emits escalation immediately and clears retained state.
3. `minimum_dwell`: raw threshold plus a two-subsequent-fresh-observation hold after entry; critical immediately enters/resets the hold. A stale row emits escalation and clears retained state.

The encoded symbol is `risk_index + 5*stale + 10*critical` (0–19). Trace enumeration order is ascending length, then lexicographic symbol tuple. Raw line format is `<base20-symbol-string>|<raw-bits>|<hysteresis-bits>|<dwell-bits>\n`; bits use `0=LOCAL, 1=ESCALATED`. The formal runner only emits these canonical rows.

**D.** `PASS_HYSTERESIS_T0_SCOPED` requires, for each stateful policy: strictly fewer switches than raw on the boundary subset (all-fresh, noncritical traces using both risks 0.5 and 0.7); zero missed same-row critical and stale events; zero extra delay on monotone fresh noncritical traces at first crossing 0.7; and exact final-mode equality with raw on every fresh noncritical trace. Any failed gate is preserved as `FAIL_SAFETY_OR_REFERENCE_GATE`; raw or independent-audit integrity failure is `STOP_AUDIT_OR_PROVENANCE`. Switch metrics are reported regardless of disposition.

**C.** Inputs are exhaustive identical symbolic traces; only policy memory differs. The thresholds/dwell are fixed here before the run and are not selected or tuned against results. Risks are synthetic levels, not calibrated probabilities. The finite comparison contains no task ground truth and cannot establish error equivalence.

**U.** Real confidence calibration, model interruption/token cost, task errors, deployment state persistence, workload-specific thresholds, and external validity remain unknown.

## One-shot rule

Run construction tests and source-hash preflight first. Then run the exact frozen formal enumerator once, followed by one separate CPU process running the independent auditor on those exact raw bytes. Preserve raw and receipt even if the decision is FAIL. No retries, parameter search, or replacement allocation.
