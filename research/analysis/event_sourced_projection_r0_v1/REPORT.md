# #1776 Event-sourced projection and checkpoint equivalence

Decision: **PASS_EVENT_SOURCED_PROJECTION_CHECKPOINT_SCOPED**

## Result

A finite deterministic reducer was evaluated over six event types:

- SET0
- SET1
- INC
- DOUBLE
- TOGGLE
- ADVANCE_GEN

State consists of an integer accumulator modulo 8, a Boolean flag and a monotone generation.

Every ordered event sequence of length 0 through 6 was exhausted:

- sequences: **55,987**
- full-fold versus incremental event-only projection mismatches: **0**

For every sequence, every prefix cut was converted into a trusted checkpoint bound to:

- the exact prefix length;
- a SHA-256 hash-chain digest of the exact prefix;
- the exact serialized prefix state;
- a trusted receipt digest over index + prefix digest + state.

The suffix was then replayed from that checkpoint:

- checkpoint resume checks: **380,713**
- checkpoint resume mismatches: **0**

## Why append-only event identity matters

Five deliberately weaker state-management schemes all have concrete divergent cases:

| Weak scheme | Divergent cases / discriminator |
|---|---:|
| index-only checkpoint alias | present |
| out-of-band mutable state write | **55,987** |
| duplicate application without sequence identity | **33,475** |
| orderless event multiset | present |
| one silently missing event | **176,948** |

Minimal witnesses are retained in RESULT.json.

For example, checkpoint index 1 can refer to prefix SET0 or prefix SET1, which produce different states. The index alone therefore does not identify a resumable state. Likewise SET0→SET1 and SET1→SET0 have the same event multiset but different final accumulator values.

## Validation controls

Sequence records fail closed for:

- duplicate sequence number;
- sequence gap;
- unknown event type.

Trusted checkpoints fail closed when, while keeping the trusted receipt fixed:

- state bytes are altered;
- prefix digest is altered;
- prefix index is altered.

All controls pass.

## Integrity

- formal invocations: **1**
- reruns / replacements / tuning after freeze: **0 / 0 / 0**
- independent audit errors: **[]**
- result digest: `ce8ad63d696a674838ae748ac83308ea8c2ee20d7a52dcca51ca5083b284b7dd`
- audit digest: `60c3a276306013accbfda2cb80c1fb06acc0a7e4988d4e3722346fd8aca8d4de`
- frozen PLAN/prove/audit hashes remained exact after formal execution
- RESULT/AUDIT Git blobs match exact local formal bytes

## Interpretation

This result supports a narrow event-sourcing invariant:

> If the reducer is deterministic, the event record is complete and ordered, mutable projection changes occur only by applying the next contiguous event exactly once, and a checkpoint is trusted and bound to the exact event prefix and state, then current state can be derived either by full fold, incremental projection, or checkpoint-plus-suffix replay without changing the result.

The result does **not** establish checkpoint authenticity against an attacker that can rewrite both checkpoint and trusted receipt. It also does not prove that a production Agent Interface event stream captures every external nondeterministic boundary. That separate completeness requirement is exactly the boundary covered by #1748.

Total ordering is sufficient here, but can be stronger than necessary when operations commute. Partial-order/event-causality compression is a separate question.

The next transfer should use one already-retained event ledger and compare full replay against checkpoint+suffix replay without re-invoking its effect owner.

No production event-store, crash-durability, storage-efficiency, GUI/model, latency, token or human-tempo claim follows from this result.
