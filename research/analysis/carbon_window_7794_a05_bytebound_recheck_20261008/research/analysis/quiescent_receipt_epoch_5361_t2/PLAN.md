# Quiescence receipt epoch binding T2

Allocation: `quiescent-receipt-epoch-5361-t2-20260930-01`
Issue: [#5361](https://github.com/Unjuno/agent-interface/issues/5361)
Predecessor failure: T1 allocation `quiescent-epoch-binding-5361-t1-20260930-01`
Frozen source main: `b0190453a787102189429e4b8c32032cf60efd17`
Branch: `research/quiescent-receipt-epoch-5361-t2-20260930`
Path: `research/analysis/quiescent_receipt_epoch_5361_t2/`

## H/T/D/C/U

**H.** Reclamation requires every registered reader's receipt to match the exact retired epoch, retired authority, and reader-registry generation. A valid current-epoch action can proceed while reclamation remains blocked.

**T.** Ten cases: complete valid bundle; receipt epoch too old/new/missing; wrong retired authority; missing reader; registry change; duplicate receipt identity; valid new action with blocked reclamation; stale action with valid reclamation.

**D.** PASS_SCOPED iff only the exact complete receipt set allows reclamation; each corruption blocks reclamation; current action and reclamation remain independent; stale action is denied; all ten rows match the separate literal oracle and direct raw invariants; no authority/effect is emitted.

**C.** Deterministic Python 3.14.5 / Darwin arm64 / stdlib. Host only; no Docker/OrbStack CLI under current coordinator hold. Runner and raw-only audit execute once each, without retries.

**U.** Synthetic protocol only: receipt labels are not cryptographic authentication; no true parallel readers, crash consistency, Linux RCU conformance, or production safety claim.
