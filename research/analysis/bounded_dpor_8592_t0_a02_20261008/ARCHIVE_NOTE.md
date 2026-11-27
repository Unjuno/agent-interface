# Issue #8592 A02 source archive

Exact package copied from branch `research/8592-dpor-t0-a02-20261008-r1` at
`bb19587730eab16061bfe4dcd1188137140f2c04`.

The Issue records one candidate invocation from the umbrella directory rather
than the Git worktree. The bind source lacked `candidate-visible/`; Python exited
1 before candidate code loaded. Candidate output and auditor invocation were
both absent. This is A02's execution-integrity failure, not a method result. The
frozen allocation was not retried. A03 is a separate completed allocation in
merged PR #8602 and does not alter A02.

No candidate, auditor, model, or GUI was run while archiving these files.
