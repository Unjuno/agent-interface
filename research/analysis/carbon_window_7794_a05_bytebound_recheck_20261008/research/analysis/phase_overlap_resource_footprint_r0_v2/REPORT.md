# #1730 phase-overlap resource-footprint serializability

Decision: **PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED**.

## Predecessor
#1720 remains retained as `FAIL_SOURCE_MATERIALIZATION`. Its first post-freeze execution did not use bytes matching the frozen Git analyzer and stopped before enumeration. It was not rerun.

## Repair
This successor changed no scientific parameter. Before execution, the local bytes for `formal.py`, `audit.py`, and `corruption.py` were converted to Git blob identities and matched exactly to the retained #1720 blobs:
- analyzer `d1f1e1200ce3077fa206a2a0ad022dbe3f9dfd48`;
- auditor `bd9a2339ee9e72fbec54d5f924bd90e69dc4749f`;
- corruption control `4446ba4ebf6c82e78443491b2bdfd87472152c7f`.

Only after all three identities matched was the fresh successor formal invoked once.

## Result
The finite model covers three logical resources, eight binary initial states, 18 deterministic read/write/increment/copy operations, and 186,624 bounded phase-program cases.

- complete-footprint overlap admitted: **51,936**
- complete-footprint candidate/oracle mismatches: **0**
- declared-conflict cases serialized: **134,688 / 134,688**
- UNKNOWN parallel admissions: **0**
- SURFACE_ONLY mismatches: **52,800**
- omitted-write declaration mismatches: **24,576**
- reversed-conflict-policy mismatches: **52,800**

The independent gate audit passes all ten checks. Four deliberate evidence corruptions are rejected.

## Why the condition is sufficient in this model
The candidate ordering is `A.input -> B.input -> A.tail -> B.tail`; the whole-intent serial oracle is `A.input -> A.tail -> B.input -> B.tail`. When A.tail has no read/write or write/write conflict with either phase of B, A.tail commutes left across B's operations without changing terminal declared-resource state or any retained per-intent read. Repeated commutation transforms the candidate into the serial oracle. The exhaustive formal checks the bounded state/operation family and finds no counterexample.

Surface identity alone is insufficient because distinct surfaces may touch one shared resource. The negative controls demonstrate this directly. A footprint declaration that omits one real shared write is likewise unsafe.

## Scope
This establishes a static deterministic serializability contract, not necessity. Conflicting operations may still commute semantically, and real applications can have hidden/dynamic resources such as clipboard, filesystem paths, focus, WM state, process environment, backend seat state, or event-loop state. No wall-time, token, model, human-tempo, or runtime-promotion claim follows.

## Next empirical discriminator
Annotate one known-independent real-XTerm overlap pair and one hidden-shared-file pair with explicit resource footprints, then test whether this contract accepts the independent pair and rejects the hidden-resource pair without changing their execution. Do not reuse or alter #1707's retained failed allocation.
