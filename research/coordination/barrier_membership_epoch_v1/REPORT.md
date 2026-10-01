# Membership-bound all-confirmed barrier aggregation

Task: `COORD-BARRIER-MEMBERSHIP-EPOCH-20260916-014`

Publication base: `33c8c538fc763fee2d05f8e5bc915888352b82b1`

Pre-measurement freeze: `9526be359f77af15414af107460eae496e64ec71`

## Decision

**`PASS_MEMBERSHIP_BOUND_ALL_CONFIRMED_SCOPED`**

The only new factor in this rung is receiver membership identity. Per-receiver barrier-confirmation semantics and ALL-confirmed aggregation are held fixed from the preceding coordination experiments.

## First outcomes

| Case | Current membership | Confirmation batch used | Decision | Final coordination |
|---|---|---|---|---|
| stable membership | epoch 1 `{A,B}` | epoch 1 `{A,B}` A/B confirmed | `ALL_CONFIRMED` | generation 2 |
| member added | epoch 2 `{A,B,C}` | retained epoch 1 `{A,B}` A/B confirmed | `HOLD_MEMBERSHIP_CHANGED` | generation 1 |
| member replaced, old batch | epoch 2 `{A,C}` | retained epoch 1 `{A,B}` A/B confirmed | `HOLD_MEMBERSHIP_CHANGED` | generation 1 at this checkpoint |
| member replaced, fresh batch | epoch 2 `{A,C}` | epoch 2 `{A,C}` A/C confirmed | `ALL_CONFIRMED` | generation 2 |

Measured state commits:

- stable coordination advance: `8760f94de24beecbc9bc5a174dc08ffbfb3ebc3a`
- added membership epoch advance: `7db64bad468c4025b94aa7f32d62bc6a9a77b79c`
- replacement membership epoch advance: `fa6cfe48e2d39cf7918050327a0ea8ef97adb6cb`
- replacement fresh-confirmation update: `4b85d0e7e7b3a0cd133513b446cdea68b3f7f5fd`
- replacement coordination advance: `5e9f1b94050907bb06e327b697b60a7c30b199e3`

Final durable coordination state is stable=`g2`, added=`g1`, replaced=`g2`.

## Interpretation

An ALL-confirmed result is not portable across receiver membership changes. The confirmation batch must be bound to the exact current membership epoch and exact member set.

In the added-member control, old A/B confirmations cannot authorize a generation advance that omits newly authoritative C. In the replacement control, old A/B confirmations are rejected after the current set becomes A/C, but a fresh current A/C batch can authorize advance without waiting on retired B.

This separates two failure modes:

1. **stale authorization** — using an old membership's confirmations after a new receiver becomes authoritative;
2. **stale dependency** — continuing to require a receiver that has left the current membership.

Exact epoch/set binding avoids both in this bounded fixture.

## Evidence boundary

Membership changes are fixture-authorized durable updates. This experiment does not establish who may change membership, how receiver membership is discovered, concurrent membership-update linearizability, quorum consensus, failure detection, or timeout eviction.

The experiment is sequential and GitHub-backed. Individual barrier installation is represented by already-defined confirmation receipts rather than rerunning #456/#449 allocations.

`verify.py` is retained deterministic checking code; no independent-agent execution is claimed.

## Remaining race / next discriminator

The aggregation decision and the coordination generation update still live in different GitHub files. Therefore a remaining TOCTOU question exists: membership can change **after** the aggregator validates a confirmation batch but **before** the coordination file is updated. Per-file GitHub SHA CAS on the coordination file alone cannot detect that cross-file membership change.

A useful next single-variable rung is to keep membership-bound confirmation semantics fixed and compare the current split-file handoff against a canonical state in which membership identity and active generation share one CAS-protected record (or an equivalent content-bound transition token). Inject one membership change between final validation and generation commit. The goal is to determine whether a stale validated membership can still authorize generation advance when the membership and generation writes are not atomically coupled.
