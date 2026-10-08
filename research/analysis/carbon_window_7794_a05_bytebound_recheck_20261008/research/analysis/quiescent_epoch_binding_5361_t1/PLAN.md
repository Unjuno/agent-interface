# Quiescent reclamation and epoch-bound action T1

Allocation: `quiescent-epoch-binding-5361-t1-20260930-01`
Issue: [#5361](https://github.com/Unjuno/agent-interface/issues/5361)
Initial registration main: `0cf275c05cc4870d17936bfcff0e8b98539c7cf2`
Frozen source main: `bbeee4da02285281e960334f8babefc2d7070358`
Branch: `research/quiescent-epoch-binding-5361-t1-20260930`
Path: `research/analysis/quiescent_epoch_binding_5361_t1/`

## H/T/D/C/U

**H.** Binding action consumption and quiescence receipts to epoch, authority, lease, and reader-set generation blocks stale in-flight work and prevents reclamation while any registered reader is unaccounted. A valid new-epoch action remains independently admissible.

**T.** Eight traces: old in-flight completion after revoke; valid new-epoch action; stale replay; wrong authority at current epoch; expired lease; crashed/unreported reader; receipt for wrong retired authority; reader registration after the snapshot. Compare `REVOKE_ONLY` and `EPOCH_BOUND`; action admission and reclamation are separate outputs.

**D.** PASS_SCOPED iff no stale/wrong-authority/expired action is consumed; exact reader-set/retired-authority/registry checks are required to reclaim; unreported/new readers block reclaim but not an independently valid new-epoch action; all 16 policy/trace rows match the independent literal oracle; no authority/effect is emitted.

**C.** Host-only deterministic finite replay, Python 3.14.5, Darwin arm64, stdlib. No Docker/OrbStack CLI under the current #5085 coordinator hold. Construction CI and formal runner/auditor are separate; each formal command runs once.

**U.** Toy protocol only: no actual concurrent threads, crash consistency, cryptographic receipt authentication, operating-system RCU behavior, or production safety. A gate result is not authority or an external effect.
