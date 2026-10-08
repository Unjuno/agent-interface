# Effect-owner manifest binding integration construction v1

Task `EFFECT-OUTCOME-OWNER-BINDING-INTEGRATION-20260916-001`, Issue #496.
Construction base: `25283e034df4241124bcd6203fd4a43994793a24`.

Decision: **`PASS_OWNER_BOUND_INTEGRATION_CONSTRUCTION`**.

## Question

Merged outcome-contract v3 binds compensation verification to the invariant manifest carried by an `ExecutionBinding`. That construction intentionally treats the binding as trusted evidence. This integration asks the next smaller question: can a concrete cooperative effect owner persist the manifest identity with the effect and expose an execution receipt from which the caller bridge derives the binding, rather than accepting an adapter-supplied binding after the effect?

## Construction

A standard-library SQLite effect owner persists four related records:

- authoritative current state;
- command content (`command_id`, invariant-manifest id, intended value, actual value);
- append-only effect/compensation events;
- execution receipt (`command_id`, invariant-manifest id, effect sequence, effect value).

For a new command, command state, authoritative effect, effect event and execution receipt commit in one `BEGIN IMMEDIATE` transaction. Exact same-content replay is read-only and returns the original receipt; same ID with different content is a conflict.

`bridge.py` accepts no free-form V3 `ExecutionBinding`. It reads the persisted owner receipt, checks it against the durable command row and authoritative effect event, then constructs V3 `ExecutionBinding(receipt.command_id, receipt.invariant_manifest_id)` itself. Post-compensation `VerificationReceipt` is also tied to that owner receipt manifest id.

The bridge pins the exact merged V3 dependency:

- bytes: 15,466;
- SHA-256 `4fd5a6001407b9e91ab3265aeca491643e035641f7926316ebf8835ba7b79449`;
- Git blob `680b104b28ba37633ec1031eac41c1945eb3aed9`.

Any dependency mismatch stops before classification.

## Test receipt

The exact publication candidate was executed in the working tree and again after clean-copy reconstruction.

- `python -m py_compile owner.py bridge.py test_bridge.py`: PASS twice.
- `python -m unittest -v`: **12/12 PASS** twice.
- source changes between runs: **0**.

Tested publication bytes:

- `owner.py`: 7,031 bytes; SHA-256 `406991f06f8e1e18385ee7f78cdc566df6d9cda674d57d898f410b489fae99ef`; Git blob `287894c6bd06bbccef5dff6ff12fd7580262cb50`.
- `bridge.py`: 2,772 bytes; SHA-256 `a9aa2653eb0f8a19dc665bd66dddacb4006334ae037181c8261dba23ed821230`; Git blob `a0e46b604f8fa1297e32d8f5864ccb3009c53814`.
- `test_bridge.py`: 5,876 bytes; SHA-256 `11d950007693af9020cfd88315c05fb5d13cf95280856ffaf674ddfee91d6d90`; Git blob `4ff8d9dc0430294602673bb32dc70428b2b0da7c`.

GitHub readback matches all three tested Git blob identities.

## Regression outcomes

The 12-test matrix establishes at construction scope:

- correct direct effect -> `EFFECT_VERIFIED`, owner receipt manifest retained;
- wrong effect + clean compensation -> `EFFECT_CONTRADICTED_COMPENSATED`;
- wrong effect + collateral-damage evidence -> `EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE`;
- post-effect primary-only manifest replacement cannot override the owner-persisted manifest id;
- exact command replay returns the original effect sequence and leaves `effect_count == 1`;
- same command id with changed content rejects and leaves `effect_count == 1`;
- unknown command has no receipt and fails closed;
- modified receipt manifest inconsistent with the durable command row fails closed;
- modified receipt effect value inconsistent with the authoritative event fails closed;
- compensation without an existing command and a second compensation both reject.

## H / T / D / C / U

**H.** Persisting the invariant-manifest identity together with the direct effect gives a model-free bridge a durable source for the V3 execution binding and prevents a later adapter from replacing that identity through the bridge API.

**T.** Cooperative SQLite owner plus deterministic bridge and tests; no live/model/GUI/game/network/user-data allocation.

**D.** `PASS_OWNER_BOUND_INTEGRATION_CONSTRUCTION`: exact V3 identity is pinned, 12/12 regressions pass twice on exact publication bytes, same-content replay is read-only, and manifest/effect tamper controls fail closed.

**C.** This assumes the SQLite owner and database are cooperative/trusted. It does not authenticate the actor that originally supplied the manifest or prove the manifest includes every real invariant.

**U.** No cryptographic signer, hostile DB writer, concurrency stress, crash/power-loss test, external service, GUI semantics, production ABI, latency, throughput or natural fault-rate claim.

## Next smallest question

Before shared-runtime promotion, carry the same owner-derived receipt shape through exactly one existing caller/executor adapter boundary and verify that no adapter layer can synthesize or replace `invariant_manifest_id`. Keep the test model-free and deterministic; do not combine it with a new live effect or planner change.
