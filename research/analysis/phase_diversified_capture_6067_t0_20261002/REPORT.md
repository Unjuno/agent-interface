# Issue #6067 T0 result

**Disposition: `PASS_METHOD_SCOPED`.** Exact enumeration of all `12^4=20,736` offset cycles found 12,546 cycles satisfying the cyclic maximum-gap cap of 18 slots. A phase cycle is selected uniformly from this admitted set and then repeats; capture count is exactly four per 48-slot superperiod. All admissible cycles have maximum adjacent capture gap ≤18 slots (observed range 1–18).

Across cue widths 1, 2 and 3 slots and all 12 fixed onset phases, the worst-phase probability of four consecutive misses under the diversified family is respectively `10001/12546`, `7672/12546`, and `5607/12546`. The fixed periodic offset has four-miss probability 1 for at least one phase at every tested width (11/12, 10/12, and 9/12 phases miss all four, respectively). Candidate and independently coded auditor agree on the full phase-specific miss vectors and schedule count; local tests pass 3/3.

This supports only the finite, idealized mechanism claim. The selected schedule remains deterministic after selection; a seed/cycle can still miss all four repetitions at a given phase, with the exact residual probabilities above. The 1.5-period gap cap is an analytic constraint, not an application-derived safety deadline. No live capture, render timing, cue semantics, task outcome, safety, or generalized probabilistic guarantee was tested. A reliable event subscription/latch may dominate phase scheduling.

PR #6093/#6086 studied hazard-shaped schedules under nonuniform onset weights. This T0 isolates repeated phase-locking of a periodic cue against fixed periodic sampling, uses uniform onset phase as a worst-phase grid, and constrains the exact maximum gap. It is not a replication or extension of the nonuniform-hazard result.

Exact bounded enumeration did not require container isolation. The local Docker Desktop Linux Engine did not return to CLI probes within 10 seconds; no container run is claimed.
