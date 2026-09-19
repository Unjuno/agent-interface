# Delayed outbox semantic revalidation — discovery block C1–C4

Status: **RETAIN plan-bound receiver validation using context incarnation + semantic predicate; HOLD general production/GUI promotion.**

Immutable base: `9088adefb48b97b79828774dd954bb8161885d59`. Successor to Issue #228 / PR #240. This block adds only `research/outbox_semantic_revalidation_v1/**`.

## Question

PR #240 retained transactional outbox + receiver idempotency for crash/retry mechanics, but explicitly left post-commit semantic revocation unresolved. Once a command is durably committed, what evidence must the receiver revalidate immediately before a delayed external effect?

## C1 — validation scope

450 cases compare dedup only, global epoch, and relevant target version.

| Policy | Stale effects | False rejects |
|---|---:|---:|
| dedup only | **50** | 0 |
| global epoch | 0 | **50** |
| relevant target version | **0** | **0** |

Deduplication is a replay property, not a semantic-validity check. A global epoch is sound but over-couples unrelated state. Relevant dependency scoping is necessary.

## C2 — exact version vs semantic predicate

400 cases hold receiver atomicity and scope fixed, changing only the validity representation.

| Policy | Stale effects | False rejects |
|---|---:|---:|
| exact target version | 0 | **50** |
| plan-bound predicate truth | **0** | **0** |

Exact version equality is unnecessarily strict when the resource changes but the action-validating predicate remains true.

## C3 — predicate truth vs logical context identity

400 cases test context A→B replacement while `action_allowed=true` in both contexts.

| Policy | Wrong-context / stale effects | False rejects |
|---|---:|---:|
| predicate only | **50** | 0 |
| context ID + predicate | **0** | **0** |

Predicate truth alone is incomplete; the plan must also bind the logical context.

## C4 — public context ID reuse

400 cases keep public context ID `A` but replace its authoritative incarnation/generation.

| Policy | Wrong-incarnation / stale effects | False rejects |
|---|---:|---:|
| context ID + predicate | **50** | 0 |
| context generation + predicate | **0** | **0** |

A reusable/public identifier is not sufficient identity evidence. In this fixture the minimum retained receiver dependency is:

`context incarnation / generation + authored semantic predicate`

Validation and effect insertion are one receiver `BEGIN IMMEDIATE` transaction in every arm. Receiver idempotency from PR #240 remains orthogonal and is not re-benchmarked here.

## Aggregate evidence

- C1: 450 cases
- C2: 400 cases
- C3: 400 cases
- C4: 400 cases
- total: **1,650 deterministic cases**
- all independent audits: zero retained-row errors
- each rung includes three deliberate audit corruptions, all rejected

Environment: Linux 6.18.44 x86_64, CPython 3.13.5, SQLite 3.46.1, five visible CPUs, batch one. No latency, throughput, token or natural-error-rate claim.

## Architecture consequence

The delayed-effect envelope is now separable into distinct concerns:

1. **sender decision durability** — transactional outbox;
2. **replay identity/content binding** — receiver idempotency key;
3. **target/context provenance** — plan-bound incarnation/generation;
4. **semantic validity** — authored predicate result relevant to the action;
5. **effect linearization** — validate those dependencies and commit the receiver effect at one coherent boundary.

These conditions do not make arbitrary external systems exactly-once. They describe what the cooperative receiver in this fixture needed to avoid the tested orphan, duplicate, stale, wrong-context and wrong-incarnation effects across PR #240 and this block.

## H / T / D / C / U

**H.** A delayed external command must carry plan-bound semantic and provenance dependencies to the receiver; replay deduplication and sender durability are insufficient.

**T.** Four single-variable rungs, 1,650 cases, separate sender/receiver SQLite DBs, sender command committed before mutation, receiver validation+effect in one transaction.

**D.** RETAIN `context incarnation + semantic predicate` as the minimal candidate in this fixture. FAIL dedup-only for staleness, HOLD global epoch and exact version as over-broad, FAIL predicate-only/context-ID-only under their targeted counterexamples.

**C.** The dependency set is authored. A missing semantic dependency, alias-resolution change, query phantom, or reused generation token can still invalidate the mechanism. Prior typed-dependency work addresses some of these discovery classes but this block does not solve them.

**U.** Cooperative local receiver; no real network/service/GUI, no crash/retry factor in these rungs, no post-delivery revocation, no automatic dependency discovery or production rate claim.

## Next boundary

Do not add another scalar dependency mechanically. The next high-information experiment should transfer this exact envelope to one existing real-application effect owner that can expose an authoritative incarnation/version and semantic predicate at commit time, or explicitly demonstrate that an ordinary GUI lacks such a commit boundary. Keep idempotency/outbox mechanics fixed.
