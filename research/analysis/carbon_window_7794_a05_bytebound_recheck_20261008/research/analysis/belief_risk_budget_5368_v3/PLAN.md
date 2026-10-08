# Risk-budgeted action-conditioned belief T0-v3

Allocation: `belief-risk-budget-5368-t0-20260930-01`
Issue: [#5368](https://github.com/Unjuno/agent-interface/issues/5368)
Registration main: `cf8ad3d1a675af9e64c1be356d03e35699548b33`
Frozen source main: `4439161abd6f8ccf276babc1c39c43428394e773`
Branch: `research/action-belief-risk-budget-5368-t0-20260930`
Path: `research/analysis/belief_risk_budget_5368_v3/`

## H/T/D/C/U

**H.** A declared 5% posterior risk budget will preserve a model-relative unsafe-mass bound while admitting some nonzero-risk cases rejected by strict worst-case admission. Expected utility and maximum-probability policies will make different risk/availability tradeoffs. Probabilities are not calibrated or authoritative.

**T.** Six base beliefs assign unsafe-state masses 0, 1%, 4%, 10%, 30%, and 80%; one separate misspecification stress reports 4% but declares actual unsafe mass 20%. Compare `MAP`, `WORST_CASE`, `RISK_BUDGET` (p≤5%), and `EXPECTED_UTILITY` (safe payoff +10, unsafe payoff −20). Enumerate exact-rational safe/unsafe branches.

**D.** Scoped pass iff all 28 policy/case rows match a separately implemented exact-rational oracle; risk-budget decisions admit exactly reported p≤5%; risk-budget admits at least one case strict worst-case rejects; expected utility follows the fixed payoff equation; the misspecification control visibly exposes actual 20% risk and is not certified safe; no authority/effect output. A failure is retained with no runner retry.

**C.** Deterministic host-only Python 3.14.5 / Darwin arm64, standard library only. Construction tests are not formal allocations. No Docker/OrbStack CLI, GUI, network, model, input, or external effect. Current #5085 disclosure requires a fresh coordinator assignment before any container CLI use.

**U.** Synthetic exact-probability arithmetic only. No calibration, model-completeness, POMDP, real-world safety, or operational benefit claim. Risk bounds are conditional on the supplied belief model; the misspecification control demonstrates this limitation.

## Frozen execution

See `FREEZE.json` for source hashes and one-shot commands. Run the formal raw runner once and independent raw-only auditor once. Preserve all outcomes; do not retune or replace this allocation.
