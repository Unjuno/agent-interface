# Issue #7857 T0 — PASS_METHOD_SCOPED

Allocation UNITIZATION-7857-T0-A01; freeze #5986815700; first outcome #5986833627 with SHA correction #5986836452. T0 ran the frozen candidate and auditor exactly once each in separate WSLc 3.0.1.0 Node 22 containers, network none, pull never, CPU 1, read-only inputs; both exit 0, retries 0.

The independent auditor reconstructed seven synthetic traces and 12/9 annotation spans. The custom exact-span match F1 was 0.4761904762, distinct from conditional category agreement (6/6). S1 training singleton/doubleton counts changed from (1,2) to (3,0), while S2 remained (4,0). Heldout new-mode episode-unit rate changed from 2/3 to 1/2. The frozen sensitivity gate flagged this instability; the exact unambiguous control stayed at F1=1 and was not flagged. Both saturation decisions remained false. All five specified mutations were rejected.

This is a synthetic deterministic method construction. Exact-span F1 is a custom boundary diagnostic, not Krippendorff's unitizing alpha or a population reliability estimate. Synthetic segmenters are not human adjudicators. No saturation decision flip, real trace-family reliability, real failure rate, causal claim, or safety evidence is shown.

The bounded T1 eligibility audit is HOLD_NO_ELIGIBLE_CONTINUOUS_TRACE; see T1-ELIGIBILITY.md and Issue comment #5986852932. It did not change the T0 result.