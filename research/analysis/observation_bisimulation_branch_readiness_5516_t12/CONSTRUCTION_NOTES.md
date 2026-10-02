# Construction notes

The first host construction-test run failed 3/3 before any candidate CLI or
formal raw invocation. The split-branch fixture exposed a trace-enumerator bug:
the prototype deduplicated by visible word alone and skipped traversal of the
second state reached by the same prefix. The candidate and independent auditor
were corrected to visit `(state, visible-prefix)` pairs; the candidate's
nondeterministic bisimulation check was also tightened to match every outgoing
successor. The frozen test set now includes the equal-trace/non-bisimilar
fixture and independently derived branch witness. This failure is a
construction defect, not evidence for or against the hypothesis; no candidate
run occurred before correction.
