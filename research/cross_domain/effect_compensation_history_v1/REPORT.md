# Effect compensation history v1

Task: `EFFECT-COMPENSATION-HISTORY-20260916-001`

Disposition: **RETAIN_HISTORY_AWARE_COMPENSATION_OUTCOME_SCOPED**.

## Question

When a direct effect is wrong, verification detects the contradiction, and a later compensation restores the current state, may the outcome be collapsed to `NO_EFFECT` because the final state matches the initial state? Or must the earlier wrong effect remain part of the result history?

This is the direct successor to Issue #427 / PR #434. That prior rung established that a direct effect can already be durable before post-effect verification fails. This rung changes one factor: whether a later compensating effect restores the current state.

## Fixture

A local SQLite effect owner contains:

- `state(id=1,value)`: authoritative current value;
- append-only `events(seq,kind,value,ns)`: effect history.

Initial state is `old`; intended result is `target`.

Three frozen scenarios:

1. `correct`: direct effect writes `target`.
2. `wrong_compensated`: direct effect durably writes `wrong`; verification contradicts it; compensation durably writes `old`.
3. `wrong_uncompensated`: direct effect durably writes `wrong`; compensation is deliberately unavailable.

History-aware outcomes are:

- `EFFECT_VERIFIED`;
- `EFFECT_CONTRADICTED_COMPENSATED`;
- `EFFECT_CONTRADICTED_UNCOMPENSATED`.

A deliberately conflated control derives outcome only from the final current state:

- final `target` -> `VERIFIED`;
- final `old` -> `NO_EFFECT`;
- anything else -> `CONTRADICTED`.

The control is not asserted to be the current product ABI.

## Construction and freeze history

A provisional pre-freeze plan accidentally executed the full 3 x 10 matrix with `r*` IDs. Those 30 rows are **construction only**, excluded from formal measurement, preserved separately, and never rerun. Formal measurement uses disjoint `m*` IDs.

Before any formal `m*` case, the source tests passed 5/5. The original pretty-printed plan SHA in the Issue body was then superseded by the exact GitHub plan serialization before measurement. Canonical plan identity:

- Git blob: `20d8340d7a8e440a785e311d39c811b8dd37591f`
- SHA-256: `4e64ac458cf5ace06309d51d45f9669988b6a7818489488ee20fb433fce274b9`
- freeze commit: `ae581faf9058be2eb84ebe9960dcfe14b55890d8`

No formal measured case had run before that freeze.

Frozen source SHA-256:

- `experiment.py`: `a91c3e3cd735cc57ee58849c8fa38114fce345cf3cfb584c7ad91c9687bfe4dc`
- `receiver.py`: `59cb59e11749dda15692e0f924fd90af4dba662ad826e2f16b52690272eab439`
- `audit.py`: `d05acbd8ab895e3120646b3b9fd09051310495277e3732adef48e977907ad462`
- `test_contract.py`: `516ec91300e9f699be35499d97001812258c740f554b5f63e9f51a44c46e04da`

## Remote premeasurement source identity defect

After formal measurement, a GitHub/local blob audit found that the `experiment.py` stored at the remote freeze commit was not byte-identical to the measured source. The remote file omitted exactly three comment-only lines; all executable statements were identical. The measured source SHA-256 had been declared in `FREEZE.json`, but the exact measured bytes were not remotely materialized until after measurement.

Posthoc checks retained this as a freeze-attestation defect rather than rerunning the allocation:

- remote prefreeze `experiment.py` Git blob: `61264f0e4309d76c1d709cdaf95ca8905b117feb`;
- reconstructed remote prefreeze SHA-256: `e6be19e54057a10a4a374f96c177c0d5f9b837cf548ef74501a5e463539d5a02`;
- measured source SHA-256: `a91c3e3cd735cc57ee58849c8fa38114fce345cf3cfb584c7ad91c9687bfe4dc`;
- textual diff: exactly three comments only;
- Python ASTs ignoring source-location attributes: equal;
- fresh three-scenario posthoc normalized outputs: equal;
- exact measured bytes were published afterward as Git blob `0b8b1af01ea4df9fd55622af566609fb8aced1ad`;
- formal measured IDs rerun: 0.

Therefore the scientific outcome is retained, but the claim “all exact executable source bytes were remotely frozen before measurement” is **false for this allocation**. The exact local measured source was hash-declared before measurement and is now published, but the remote byte-attestation defect remains explicit.

## Formal result

30 first outcomes: 10 repetitions per scenario, one execution per `m*` ID.

| Scenario | Current state at end | Retained history | History-aware result | Final-state-only result | History-truthful |
|---|---|---|---|---|---:|
| correct | `target` 10/10 | `effect:target` 10/10 | `EFFECT_VERIFIED` 10/10 | `VERIFIED` 10/10 | 10/10 |
| wrong_compensated | **`old` 10/10** | **`effect:wrong -> compensation:old` 10/10** | **`EFFECT_CONTRADICTED_COMPENSATED` 10/10** | **`NO_EFFECT` 10/10** | **0/10** |
| wrong_uncompensated | `wrong` 10/10 | `effect:wrong` 10/10 | `EFFECT_CONTRADICTED_UNCOMPENSATED` 10/10 | `CONTRADICTED` 10/10 | 10/10 |

History-aware labels matched persisted SQLite state/history **30/30**. Final-state-only classification was history-truthful **20/30** overall and **0/10** in the compensated stratum.

The important result is not that compensation failed; it succeeded in its declared narrow purpose 10/10 by restoring current state to `old`. The result is that **restored current state and historical no-effect are different claims**.

## Mechanism interpretation

A compensation is itself another effect. In the compensated rows, two durable events occurred in order:

1. wrong effect: `old -> wrong`;
2. compensating effect: `wrong -> old`.

Therefore a result that says only `NO_EFFECT` erases an observed causal fact. A truthful outcome needs at least two dimensions:

- whether the intended effect was verified or contradicted;
- whether subsequent compensation restored the declared current-state invariant.

`EFFECT_CONTRADICTED_COMPENSATED` records both without pretending that the wrong effect never occurred.

This does **not** imply that compensation makes a task safe in general. Real compensation can fail, be partial, be stale, or introduce collateral effects. This rung measures only one scalar current state plus append-only history.

## Validation

Separate extraction of the raw evidence archive verified:

- formal measured case directories: 30;
- same formal ID reruns: 0;
- archive manifest files: 71;
- manifest hash/size mismatches: 0;
- independent audit replay: byte-identical;
- source SHA-256 values in the raw archive: 4/4 exact;
- canonical plan SHA-256: exact;
- tests after extraction: 5/5 PASS.

Posthoc corruption controls were run only on copied evidence. The auditor rejected 5/5 corruptions independently: phase-label flip, final-state-only label flip, deletion of the wrong-effect history event, final-state corruption, and reversed timestamps. Formal evidence was not modified.

Raw evidence archive:

- `effect_compensation_history_evidence.tar.xz`
- bytes: 12,524
- SHA-256: `944d14c37088f1a1b11e83b0e10ce5eaaab20fd8af5d6284bac38da14e4046f8`

## Environment

- AMD EPYC 9V74 80-Core Processor; container affinity CPUs 0-4
- CPython 3.13.5
- SQLite 3.46.1
- Linux 6.18.44 x86_64 / glibc 2.41
- single-case sequential execution

No performance claim is made.

## H / T / D / C / U

**H.** Successful compensation can restore current state without erasing the fact that a wrong direct effect occurred.

**T.** Frozen 30-case SQLite block with three scenarios, append-only effect history, independent replay, and no same-ID reruns.

**D.** RETAIN the scoped history-aware compensation outcome. Final-state-only `NO_EFFECT` is rejected as historically false for the compensated stratum.

**C.** A system whose semantics intentionally care only about current state may not need the full history for every decision. But it still must not use `NO_EFFECT` if that label is interpreted causally or for audit/retry policy.

**U.** Local cooperative SQLite fixture, authored compensation, one scalar state. No claim about GUI undo, external messages, financial effects, network services, power loss, mathematical reversibility, compensation side effects, automatic semantics, or production ABI.

## Next rung

The next smallest unresolved question is whether a compensation can restore the primary target while damaging a preserved/collateral property. That would test whether `..._COMPENSATED` itself needs independent verification of both the restored invariant and forbidden collateral effects, rather than being inferred from the primary final value alone.
