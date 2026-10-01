# #1643 Plan — real versus cosmetic multi-cursor parallelism

## H
For already-authorized non-preemptive operations, logical cursor multiplicity reduces actuator makespan only when lowering exposes at least two concurrently usable non-conflicting actuator resources (or an atomic backend primitive with genuine simultaneous semantics). If all operations require one exclusive pointer-state resource, no number of logical cursors can reduce actuator makespan below the sum of their pointer service times.

## T
Analytic proof plus deterministic exhaustive integer-time scheduling check. Enumerate every 3-operation case with durations in {1,2}, every forward-edge DAG on edges 0→1, 0→2, 1→2, and resource masks {P}, {K}, {P,K}: 1,728 cases. Validate lower bounds and search for any same-pointer counterexample. Retain canonical examples for aliased pointer, independent pointers, pointer+keyboard, dependency-dominated work, and atomic two-contact gesture.

No model, GUI, network, or shared runtime mutation.

## D
PASS_SCOPED iff lower-bound violations=0, aliased-pointer counterexamples=0, and at least one disjoint-resource strict-speedup construction exists.

## C
Even with independent input resources, an application event loop/effect pipeline can serialize task effects; task dependencies can dominate; OS seats may merge multiple virtual pointers into one pointer state; safety policy may intentionally serialize authority.

## U
The exhaustive check is bounded and the theorem is under an explicit exclusive-resource/non-preemptive model. It does not prove any particular OS/backend exposes multiple independent pointers. Live transfer must measure device identity, simultaneous delivery, effect overlap, release, and authority semantics.
