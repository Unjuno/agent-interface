# Effect phase contract: pre-effect rejection is not post-effect contradiction

Decision: **RETAIN_PHASE_DISTINCTION_SCOPED**. Issue #427. Publication base `9558313ed704804031733031f9e9443ddffc54de`; premeasurement freeze `b999f2770fb3d2505d9870dd66d6043d1ca8d9b7`.

## Question

The preceding stageable-artifact work can inspect a private candidate and refuse publication before authoritative state changes. That semantic does not automatically transfer to a direct effect, where independent verification may happen only after an effect owner has already committed something.

This rung asks one narrow result-contract question: can the same terminal `REJECTED_NO_EFFECT` meaning truthfully cover both phases? The compared label is an intentionally conflated control vocabulary, **not a claim about the current Agent Interface production baseline**.

## Fixture and freeze

Two local generated effect classes share requested value `desired`:

- `stageable`: write a private candidate file, validate its value, then atomically replace the authoritative file only when valid;
- `direct`: invoke a separate CPython/SQLite effect-owner subprocess. Its transaction immediately inserts one durable effect row. The authored `wrong` condition stores `wrong` and exits successfully; verification occurs after the process returns.

Five tests passed before measurement. Before the first measured case, the initially mentioned local pretty-JSON plan and uploaded GitHub plan were found to differ only in JSON layout. Measured count was still zero. GitHub plan bytes became canonical: blob `4c104b84961bef8697806f789cdc33f9691ddb1a`, SHA-256 `f5e6c8e642e4cbbdaca3a11f352498a327553c0a25b08adb9f7e1e8562155d82`. Cases, order, sources, hypotheses and gates did not change.

Formal allocation: 40 first outcomes = 10 repetitions x two effect classes x two behaviors. No measured ID was rerun.

## Results

| Effect class / behavior | n | Effect present | Phase-aware truthful | `REJECTED_NO_EFFECT` truthful when used |
|---|---:|---:|---:|---:|
| stageable / correct | 10 | 10 | 10/10 | 10/10 |
| stageable / wrong | 10 | **0** | 10/10 | 10/10 |
| direct / correct | 10 | 10 | 10/10 | 10/10 |
| direct / wrong | 10 | **10 wrong durable effects** | 10/10 | **0/10** |

Phase-aware outcomes are `PUBLISHED_VERIFIED`, `REJECTED_PRE_EFFECT`, `EFFECT_VERIFIED`, and `EFFECT_CONTRADICTED` for the four cells respectively. Overall phase-aware state description is 40/40 consistent with retained authoritative state. The deliberately conflated control label is truthful on 30/40 traces and false on all ten direct-wrong traces because it says `NO_EFFECT` after a wrong effect has already been durably inserted.

The discriminator is not task-success classification: both vocabularies know direct-wrong failed its desired postcondition. The difference is whether the terminal result truthfully describes **effect occurrence and phase**. A verifier cannot retroactively turn an already-applied wrong effect into a pre-effect rejection.

## Interpretation

For a stageable operation, candidate contradiction can legitimately yield a no-authoritative-effect result when publication never occurs. For a direct operation, post-effect contradiction must preserve the fact that execution/effect may already have happened. Therefore a generic result contract should not let `rejected` imply `no effect` unless evidence establishes rejection before the effect boundary.

This supports a distinction such as pre-effect refusal versus verified effect versus contradicted effect. It does **not** establish that these exact strings are the production ABI, nor that every direct effect is irreversible. The SQLite row is technically mutable by a later compensating operation; compensation was not tested.

## Verification

The independent auditor imports no experiment module. It reads the authoritative stageable file or SQLite effect table and recomputes expected phase/result truth. Fresh archive extraction reproduced the audit byte-for-byte and reran all five tests successfully.

Raw-evidence manifest: 100 files, 314,731 payload bytes; zero hash/size mismatches after extraction. Raw archive `effect_phase_contract_evidence.tar.xz`: 11,268 bytes, SHA-256 `1f6fb594f7f10ed1c3fe66d10e22a65b9a421a21677d5909d326d62ea65b30c4`.

## H / T / D / C / U

**H.** A post-verification failure on a direct effect cannot truthfully be represented as `REJECTED_NO_EFFECT` when a wrong effect is already durable.

**T.** Frozen 40-case local file/SQLite matrix with a separate direct effect-owner subprocess, first outcomes retained and independent persisted-state audit.

**D.** RETAIN the scoped phase distinction. Stageable wrong leaves no authoritative effect 10/10; direct wrong leaves a wrong effect 10/10; phase-aware labels match state 40/40.

**C.** The discriminator uses an authored wrong receiver. A contract could use different vocabulary that is equally truthful; this experiment does not rank names. Compensation/idempotency can alter recovery behavior without changing the historical fact that an effect occurred.

**U.** One local host, generated file/SQLite fixture, no asynchronous unknown state, no external service, no crash/power-loss, no GUI, no natural failure probability, no performance estimate. Direct here means effect-before-verification, not mathematically irreversible.

This result composes with Issue #34's effect-outcome direction and Issue #16's partial/compensation vocabulary, but does not execute those broader proposals. The next discriminating question is whether a later verified compensation may change the current state without erasing the historical `EFFECT_CONTRADICTED` event.
