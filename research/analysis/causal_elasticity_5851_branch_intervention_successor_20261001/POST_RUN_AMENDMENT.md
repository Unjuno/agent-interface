# Post-run amendment — outcome and correction

The frozen successor H was falsified by its one independent enumeration; the result is **not** `PASS_COUNTEREXAMPLE`.

For the frozen branch-change fixture, the base displayed path costs 130 ms versus declared alternate endpoint 260 ms. Halving model cost yields 80 ms versus 260 ms, so the same displayed path remains critical and its endpoint delta is 50 ms. The separate +80 ms intervention yields 210 ms versus 260 ms, also without a route switch under these numeric fixture values. The preregistered criterion is therefore `FAIL_NO_COUNTEREXAMPLE` for the proposed half-cost defect.

The original candidate reports no numeric half-model delta (null) and sets the half-model intervention status to `NONSTATIONARY_INTERVENTION`; it does not make the hypothesized invalid numeric claim. The case-level status and +80 ms branch rule are overconservative or inconsistent with the explicit 260 ms alternate endpoint. That is a fixture/rule consistency question for a new, separately frozen successor. This does not undermine the original T0's finite calculations on its hand-authored graph, but it narrows the earlier concern.

Candidate was not rerun, original candidate/auditor/raw remain untouched, and no result was pooled into the original allocation. The independent enumeration itself is recorded in `CANDIDATE_RESULT.json`.
