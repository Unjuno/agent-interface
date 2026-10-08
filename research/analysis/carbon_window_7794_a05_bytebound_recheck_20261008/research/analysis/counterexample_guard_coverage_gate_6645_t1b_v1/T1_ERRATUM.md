# Erratum for Issue #6645 T1 — preserved predecessor limitation

The merged T1 package at
`research/analysis/counterexample_guard_coverage_gate_6645_t1_v1/` and its
first-outcome raw/hash evidence are not modified. Independent post-merge review
found that T1's candidate source directly checks `modal_occlusion` after its
coverage-gate precheck, while the comparator `legacy_decide` omitted that
predicate. Therefore the observed `legacy=ADMIT` versus `candidate=UNKNOWN`
does not isolate the coverage gate: disabling the gate in the same T1 candidate
would still reach the direct modal check and refuse the harmful row.

T1b fixes the comparison by providing candidate-visible observations with no
modal value for the hidden family and running the same candidate predicate loop
with only the coverage gate toggled. The oracle labels and hidden truth are in a
separate input used by the independent auditor only. T1's original outcome is
retained as historical data; T1b is a distinct successor allocation, not a
rewrite or rerun of T1.
