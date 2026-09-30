# Issue #5318 â first construction allocation

Allocation: `semantic-serializability-fsm-r0-20260930-01`
Intake main: `c4735cfd27bfca057d9c1fca9a7ea19866f77259`
Branch: `research/semantic-serializability-5318-20260930`
Proposed additive repository path: `research/concurrency/semantic_serializability_5318_v1/`

## H/T/D/C/U

**H.** For the frozen finite action set below, raw syntactic coalescing produces at least one illegal/order-dependent effect, while a conservative semantic-footprint gate produces none. On truly disjoint/commuting actions it admits more parallel pairs than global serialization. Missing or incomplete footprints are treated as conflicts, never as permission.

**T.** One deterministic, no-model construction allocation in a network-disabled OrbStack container. Two fixed actions have explicit read/write sets and one known initial state. Enumerate both serial schedules and the concurrent schedule. Compare `RAW_COALESCE`, `GLOBAL_SERIAL`, and `SEMANTIC_GATE` against an independent state-transition oracle. Include disjoint commutative increments, same-key increments, read/write order dependence, a hidden read omitted from one declared footprint, and unknown footprint. Preserve each proposal, declared footprint, actual footprint (oracle only), schedule, effects, final state, policy decision, and source/image identity. No random seed, retries, external services, GUI, model, or real side effect.

**D.** This first rung is a scoped PASS only if every case reconciles, RAW_COALESCE exposes at least one counterexample, SEMANTIC_GATE has zero illegal concurrent admissions and zero oracle divergence, and it admits at least one known-disjoint pair rejected by GLOBAL_SERIAL. The independent raw-only auditor must report zero errors and reject all frozen corruptions. Any disagreement is retained as FAIL/STOP, not tuned away.

**C.** Synthetic finite-state oracle; no Agent Interface runtime change, authority grant, external effect, model, GUI, network, or user data. Abstract serializability is not proof of real-world transactionality.

**U.** This is one hand-authored finite construction suite, not a generated population or proof that real footprints are complete/trustworthy. No latency/throughput or production benefit claim.

Frozen decisions: run one candidate invocation and one separate audit invocation; preserve raw bytes and SHA-256; no outcome-driven source changes; no reruns of this allocation.
