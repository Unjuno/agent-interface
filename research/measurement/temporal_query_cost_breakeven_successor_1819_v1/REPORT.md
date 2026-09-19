# Temporal query cost break-even successor (#1952)

Decision: PASS_TEMPORAL_QUERY_COST_BREAKEVEN_SUCCESSOR_SCOPED

Frozen constants:
- UNIVERSAL_FIXED: [11, 11, 11, 11]
- CLASS_ONLY: [4, 2, 8, 6]
- CLASS_ANCHOR: [4, 2, 2, 2]
- Prior simplex denominator: 40; complete enumeration: 12,341 points
- Candidate SHA-256: d2397a0d2ada052820cb96b898cfb99db112f65c27df637d686c8689e37e2150

Results:
- CLASS_ONLY expected image budget extrema: [2, 8]
- CLASS_ANCHOR expected image budget extrema: [2, 4]
- Anchor saving: (6*EVENT + 4*REVERSAL)/40; zero iff both masses are zero
- Equal-prior thresholds: 6, 5/2, 17/2 image-cost units
- Candidate and independent auditor agree over all 12,341 priors
- Budget, prior-normalization, EVENT coefficient, REVERSAL coefficient, and inequality-direction corruption controls: PASS
- Formal invocations: 1; reruns/replacements/tuning: 0

Scope and stop:
This is exact symbolic accounting only. It does not establish model usability, token savings, latency, GUI correctness, or runtime policy. No model/provider/GUI/X11/network/task input was used. Stop after this frozen result; an empirical successor must measure actual query overhead and marginal image cost before runtime selection.
