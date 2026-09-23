# #1702 Evidence-dependent compute decision lattice

H: compose completed REUSE, hard-feasibility and expected RUN/WAIT results in strict layers. Cached exact+unexpired=>REUSE; cached mismatch=>REBUILD_REQUIRED; cached exact expired=>DROP_EXPIRED. Active mismatch=>CANCEL_STALE; active current tardy=>CANCEL_TARDY; only active current timely jobs reach RUN/WAIT/TIE expected selector.
T: exact typed state grid, independent oracle, edge/corruption controls, source freeze, one formal invocation.
D: candidate/oracle mismatch0; invalid reuse/rebuild/hard override/selector mismatch/bypass0; one typed disposition per row; formal1/reruns0.
C: exact version match inherits #1675 assumptions; p/g/w uncalibrated; rebuild cost/multijob/preemption/partial results out of scope.
U: analytical composition only; no runtime performance/ABI/product claim.
