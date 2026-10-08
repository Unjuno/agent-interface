# Post-run correction

The original proposed successor result was initially drafted as `PASS_COUNTEREXAMPLE` before checking the actual candidate's branch-change output. That draft conclusion was wrong and is superseded by this correction; preserve it in the predecessor branch as provenance.

The frozen result shows the candidate returns `paired_endpoint_delta_ms: null` and `intervention_status: NONSTATIONARY_INTERVENTION` for halving the model region. Independent cost enumeration gives 80 ms on the displayed path and 260 ms on the declared alternate, so the selected route does not change and the proposed numeric-invalidity counterexample fails.

The candidate's broader case-level status and the declared +80 ms `branch_rule` remain inconsistent/overconservative relative to those costs (210 ms versus 260 ms), which motivates Issue #5911. This is a synthetic fixture semantics issue, not a runtime defect. Original #5851 T0 and all source/raw/audit artifacts remain unchanged.
