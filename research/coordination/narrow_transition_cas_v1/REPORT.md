# Narrow transition CAS versus unrelated-state contention — retained result

Task `COORD-NARROW-TRANSITION-CAS-20260916-017`, Issue #487. Publication base `defb76363803ac76875924b7246de76a1f6d6963`; source-first freeze head `f1728513199447c22bd29bb23cd4e386e87e8a9b`.

## Decision

**`PASS_NARROW_TRANSITION_CAS_SCOPED`.**

The experiment changes only the CAS footprint. A wide canonical record that includes transition-relevant state plus unrelated metadata safely rejects a stale generation transition after metadata-only change, but that rejection is false contention with respect to the declared transition semantics. Moving only `membership_digest` and `active_generation` into the transition CAS record allows the same valid transition after unrelated metadata changes, while a membership-digest change still invalidates the old transition.

## First outcomes

| Case | Intervention | Measured generation commit | Final state |
|---|---|---|---|
| wide_unrelated | note revision 1 -> 2 in same wide record | old-SHA write HTTP 409 | D1 / g1 / note2 |
| narrow_unrelated | separate metadata note1 -> note2 | narrow D1/g1 -> D1/g2 succeeds | transition D1/g2; metadata note2 |
| narrow_membership | narrow D1/g1 -> D2/g1 | old-SHA D1/g2 write HTTP 409 | D2/g1 |
| narrow_stable | none | narrow D1/g1 -> D1/g2 succeeds | D1/g2 |

Measured successful commits:
- wide metadata update: `ae5a848094b2b42f5a443a08d39a8148a2923508`
- narrow unrelated metadata update: `4d086677c7ee1d8b94d0b73077dd9804bc9f93df`
- narrow unrelated generation advance: `2aa1f06be818c015466cfa2fb01a7fdaf4a91207`
- narrow membership change: `45ca5e1f14d1606d9185077bccac085761c38d52`
- narrow stable generation advance: `25f2ce8ac6cd14f60cf48b83b7753655afeee4f4`

Both prescribed stale writes received GitHub Contents API HTTP 409 stale-content rejection. Fresh-SHA retry count is zero.

## Interpretation

The relevant principle is not “put everything in one file.” It is **bind one semantic transition to one CAS identity whose footprint contains all and only state that can invalidate that transition**. Too narrow is unsafe; too wide is safe but can create avoidable contention. This is the same read/write-footprint problem previously observed in delayed Git publication, now applied to coordination authority.

## Limits

`note_revision` is authored as genuinely unrelated. The experiment does not discover dependency sets. Sequential prescribed GitHub interleavings only; no simultaneous requests, distributed consensus, membership-change authority, confirmation freshness, crash/power loss, latency/rate, or production protocol claim.
