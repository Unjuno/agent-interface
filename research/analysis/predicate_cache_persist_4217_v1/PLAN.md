# Successor #4217 — dependency-bound predicate cache persistence across process restart

## Changed scientific factor

#4217 established scoped in-process dependency-scoped predicate reuse on a deterministic replay trace. This successor changes only the lifecycle boundary: serialize a predicate cache artifact, terminate the preparing process, and let a fresh process decide whether it may reuse the artifact under current dependency/intent/producer/source generations.

This experiment assumes the declared dependency set is complete. It does not test hidden-dependency discovery.

## H

A serialized semantic-predicate cache can be reused across process restart without semantic/provenance stale reuse when the artifact schema/digest and the exact declared dependency key match the current state. A value-only persistent cache will expose stale reuse when dependency, intent, producer, source generation, or currentness changes. A semantic ABA with a new generation must miss even when the recomputed truth is numerically identical.

## T

Provided Linux x86_64 execution container, CPython 3.13.5, standard library only. No GUI/input/model/provider/network/user data/shared-runtime mutation.

Policies:
- `VALUE_ONLY_PERSIST`: reuse any retained TRUE/FALSE/UNKNOWN value without dependency validation.
- `DEPENDENCY_BOUND_PERSIST`: reuse only a valid artifact with an exact current dependency key; otherwise recompute from current state.

Eight frozen scenarios: SAME, IRRELEVANT_CHANGE, FORM_DEP_CHANGE, SEMANTIC_ABA_NEW_GENERATION, INTENT_CHANGE, PRODUCER_CHANGE, SOURCE_REPLACED, SOURCE_STALE. Three repetitions × eight scenarios × two policies = 48 consumer rows. Each scenario/repetition uses a fresh preparing process; every policy evaluation is a fresh consumer process. Thus the scored cache boundary is cross-process serialization/reload, not an in-memory Python object reuse.

Four malformed-artifact candidate controls: BOOL_VERSION, BAD_DIGEST, MISSING_KEY, WRONG_SCHEMA. Construction tests are excluded. Freeze source/plan/case/audit/control/environment identities publicly before exactly one formal runner invocation. The formal result file refuses overwrite. No row retry/replacement/pooling or post-result gate/source tuning.

## D

`PASS_PREDICATE_CACHE_RESTART_PERSISTENCE_SCOPED` only if all of the following hold:
- 48/48 exact scheduled rows and 4/4 malformed controls with observed child exits 0 and empty stderr;
- independent audit recomputes predicate truth/current dependency equality from primitive states rather than trusting candidate oracle fields;
- candidate value correctness 48/48;
- candidate stale dependency-key reuse 0;
- candidate exact-key hits exactly 6 (SAME and IRRELEVANT_CHANGE × 3 repetitions); all other rows recompute;
- VALUE_ONLY_PERSIST hits 48/48, has exactly 9 wrong-value rows, 6 unsafe executable TRUE rows against non-TRUE current truth, and 18 stale-provenance reuse rows;
- malformed artifacts are not reused and current truth is returned;
- 10/10 copied-evidence corruption controls reject;
- frozen source identities remain unchanged after formal.

Any stale candidate reuse or executable candidate disposition from non-TRUE current truth is scientific FAIL. Missing/source/process/evidence ambiguity is STOP/HOLD. A negative comparator finding remains separate from the candidate boundary PASS.

## C

The artifact SHA-256 is an integrity check, not authentication. The dependency set is authored and assumed complete; hidden dependencies remain a separate problem. Exact generation equality may over-invalidate semantically equivalent new generations by design. The predicate and states are deterministic synthetic fixtures. JSON serialization cost is not a performance gate.

## U

No crash-atomic artifact publication, power loss, multiwriter/concurrent readers, filesystem durability, malicious artifact origin, cross-platform/version transfer, learned predicate/model behavior, token/latency/task benefit, live action authority, production promotion, #57/#2789 integrated acceptance, or repository-roadmap completion.

## Bounded roadmap

Collision check -> excluded construction -> successor Issue + additive branch/path -> public source/gate freeze/readback -> one formal invocation -> raw-only audit + corruption controls -> additive complete source/raw/report PR -> exact-head CI/review -> merge only if qualified -> main readback -> delete only owned branch if dependency-safe and connector supports ref deletion.
