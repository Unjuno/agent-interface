# Outbox semantic revalidation v1 — C1

Status: **RETAIN relevant-context validation; FAIL dedup-only for semantic staleness; HOLD global epoch as over-broad.**

Immutable base: `9088adefb48b97b79828774dd954bb8161885d59`. Scope: `research/outbox_semantic_revalidation_v1/**` only. Successor to Issue #228 / draft PR #240. No shared runtime, model, GUI, external service or user data.

## Question

A sender can durably commit an outbox command and deliver it later. PR #240 established rollback/recovery/idempotency mechanics but explicitly left post-commit semantic revocation open. C1 asks what the receiver must revalidate when relevant or irrelevant context changes between sender commit and receiver effect.

## Frozen comparison

Three receiver policies:

1. `dedup_only`: content-bound idempotency key only;
2. `global_epoch`: require the whole receiver context epoch to equal the plan-time epoch;
3. `relevant_version`: require only the target resource version named by the command dependency.

Three schedules: stable, relevant target change, unrelated resource change. Fifty repetitions per policy/schedule = **450 deterministic cases**. Each case creates a durable sender SQLite outbox and a separate receiver SQLite database. Sender commit occurs before mutation. Receiver validation and effect insertion share one `BEGIN IMMEDIATE` transaction.

Ground truth is intentionally narrow: stable and unrelated change should effect; relevant target change should reject.

## Result

| Policy | Cases | Effects | Stale effects | False rejects |
|---|---:|---:|---:|---:|
| dedup only | 150 | 150 | **50** | 0 |
| global epoch | 150 | 50 | 0 | **50** |
| relevant target version | 150 | 100 | **0** | **0** |

Deduplication prevents replay identity conflicts but says nothing about semantic validity of a unique delayed command. A global epoch is safe in this fixture but rejects every unrelated context change. Binding the command to the relevant target version preserves all 100 permitted effects and rejects all 50 relevant mutations.

## Audit

`audit.py` re-derives the ground-truth effect/reject rule from scenario and retained pre-delivery context; it does not call the runner's delivery policy. All **450/450** retained rows have no audit errors and the recorded receiver decision snapshot equals the pre-delivery authoritative context. Three deliberate corruptions are rejected: sender durable flag, decision/effect-count inconsistency, and context snapshot corruption.

Executed source SHA-256:

- `runner.py`: `ebb73e795bcafe83e12131c5bb9108224073879f18b166ff3b4d160797c47ca6`
- `audit.py`: `59096243038493ec35cb65e39be2072e105803e07f4117006122595dd16b76f2`

Environment: Linux 6.18.44 x86_64, CPython 3.13.5, SQLite 3.46.1, five visible CPUs, batch one. No timing claim.

## H / T / D / C / U

**H.** Receiver-side idempotency alone is insufficient for delayed-command validity. Revalidating the plan-bound relevant target version at the receiver effect boundary prevents post-commit stale delivery without coupling the command to unrelated state.

**T.** 450 cases, one receiver transaction per effect decision, exact three-policy/three-schedule matrix, first completed allocation retained.

**D.** `relevant_version` PASS for C1 (stale 0, false reject 0). `dedup_only` FAILS semantic validity (50 stale effects). `global_epoch` is safe but over-broad (50 false rejects).

**C.** Relevant-version equality may itself be stricter than the semantic validity condition. A target can change version while the predicate that made the action valid remains true.

**U.** Authored dependency, cooperative local SQLite receiver, no dependency discovery, network, crash/retry factor, GUI, post-delivery revocation or natural frequency claim.

## Next smallest rung

C2 changes exactly one thing: replace exact target-version validation with the authored **semantic predicate result** when target version changes but the action-validating predicate remains true. Compare exact-version against predicate-truth validation; keep receiver transaction, outbox, command ID/content binding and effect logic fixed.
