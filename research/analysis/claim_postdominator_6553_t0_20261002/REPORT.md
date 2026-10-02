# Issue #6553 T0 — claim-scoped postdominator placement

**Result: `PASS_METHOD_SCOPED` (finite synthetic fixture only).** The pinned
WSLc candidate and independent auditor each ran once; both exited 0. Construction
tests passed 8/8 before and after the formal run. See `FREEZE.json`,
`results/formal-01/RUN_RECORD.md`, the raw paths and the independent audit.

The positive two-route fixture selected the typed shared semantic check at total
cost 3.0 versus route-local cost 6.0, preserving all finite claim paths. The
bounded loop/no-gain control kept route-local checks at 6.0, equal to its
baseline. The graph-only optimizer chose a cheaper dispatch checkpoint (1.5 in
the positive case), but the independent auditor found it semantically unsound.
Wrong-target, stale-generation, hidden-effect, incomplete-graph and early-claim
controls were not promoted to a successful shared claim. Independent path
enumeration found three claim paths in the complete oracle for the deliberately
incomplete graph, against two in the candidate graph.

This is a method result over stipulated finite graphs and costs. It does not
establish real GUI graph closure, application-oracle adequacy, runtime savings,
action safety, or novelty of the general graph-placement idea. The placement
and end-to-end verification aspects have prior art; the exact typed/fresh
GUI-claim transfer remains unverified beyond this fixture.

WSLc emitted a kernel warning that cgroup was not mounted and swap-limit
capabilities were unavailable; it reported memory limited without swap. The
assay completed, but strict RAM/swap enforcement is not claimed. Full commands,
exit codes, warning, outputs, and no-retry record are in the run record.
