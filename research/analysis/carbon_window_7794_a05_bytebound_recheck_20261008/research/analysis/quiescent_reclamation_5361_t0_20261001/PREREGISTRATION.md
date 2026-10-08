# Quiescent reclamation of revoked readers — T0 finite-state replay

Issue #5361 proposes separating removal (stop new acquisitions) from reclamation
(prove no prior reader can still use an old authority epoch).

## H / T / D / C / U

**H.** With two readers and one revoker, revoke-only semantics can declare an
epoch reclaimed while an already acquired reader can still use it. A
quiescence-aware protocol must keep the object `QUIESCING` while any old reader
is active, accept only current-epoch quiescence, and reject old-epoch use after
quiescence or an explicit newer-generation fence.

**T.** Deterministic finite-state exploration of all reachable states and
transitions for two readers under the event alphabet `acquire(r0/r1)`,
`remove`, `use(r0/r1)`, `quiesce(r0/r1)`, stale-epoch `quiesce(r0)`, and
`fence(new_generation)`. Compare a revoke-only baseline that treats REMOVE as
immediate reclamation with a two-phase protocol. Retain reachable-state and
transition counts, shortest counterexample witnesses, and transition refusal
reasons. A separate raw-only checker independently re-enumerates the graph.

**D.** `PASS_METHOD_SCOPED` iff the baseline has a reachable old-reader use
after its immediate-reclaim point; the two-phase protocol never admits use
after actual reclamation; reclamation does not occur with an active unfenced
reader; stale quiescence cannot discharge a current reader; and a newer
generation fence blocks old-generation use. Otherwise `FAIL` with a retained
counterexample. This is finite protocol-model evidence, not a runtime result.

**C.** CPython 3.11.9, Windows host CPU, standard library only. No Docker,
GPU/CUDA, model, network, GUI, OS input, or external side effect; the shared
Docker/OrbStack lane has no allocation for this task. Source/main/path are
frozen before one runner invocation and one separate audit; no retries.

**U.** The model assumes a complete reader set, trusted current-generation
fence, and truthful reader quiescence. It does not model crashes, malicious or
unregistered readers, network partitions, side effects already dispatched,
wall-clock leases, fairness, or implementation-level memory reclamation. No
production safety or availability guarantee follows.

## Frozen transition semantics

- Reader states are `NEVER`, `ACTIVE`, `QUIESCENT`, or `FENCED`.
- REMOVE blocks later acquire calls but does not invalidate work by an
  already-active reader.
- Current-epoch QUIESCE is accepted only for an ACTIVE reader.
- A stale-epoch quiescence receipt is a no-op and cannot change reader state.
- A generation fence marks every ACTIVE old-generation reader FENCED and
  rejects subsequent old-generation USE.
- Two-phase RECLAIM occurs after REMOVE only when no reader remains ACTIVE.
- USE is legal during QUIESCING while its reader remains ACTIVE, but is
  rejected after that reader becomes QUIESCENT/FENCED.
- The baseline incorrectly equates REMOVE with RECLAIM and continues allowing
  old ACTIVE readers to USE.

The only accepted result label is scoped to this exhaustive two-reader model.
