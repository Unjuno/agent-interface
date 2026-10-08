# Result — risk-budgeted action-conditioned belief T0-v3

Allocation: `belief-risk-budget-5368-t0-20260930-01`
Issue: [#5368](https://github.com/Unjuno/agent-interface/issues/5368)
Frozen source main: `4439161abd6f8ccf276babc1c39c43428394e773`

## H/T/D/C/U outcome

**H — PASS, scoped/model-relative.** Across 28 rows (seven cases × four policies), independent audit returned `PASS_READONLY`, no errors, and exact rational decisions/branch weights/payoffs matched the independent oracle. The 5% `RISK_BUDGET` admitted four cases versus one for strict `WORST_CASE`; it admitted the three base beliefs at 0%, 1%, and 4%, plus the misspecification stress reported as 4%. Thus it trades worst-case abstention for nonzero posterior risk.

`EXPECTED_UTILITY` admitted six cases under the fixed `+10/-20` payoff (positive expected utility iff reported unsafe mass < 1/3). `MAP` also admitted six in this deliberately chosen corpus. Neither gate enforces the 5% risk ceiling.

The misspecification stress is decisive scope evidence: the budget gate admitted reported unsafe mass 4% while the declared actual unsafe mass was 20%; the raw record flags this discrepancy. Therefore the 5% result is conditional on model correctness and is not a real-world safety guarantee. No authority or external effect was emitted.

**T/C:** One frozen exact-rational host run, Python 3.14.5 / Darwin arm64 / stdlib. Formal runner and raw-only auditor each invoked once. No Docker/OrbStack CLI, network, model, GUI/input, or external effect; the current #5085 disclosure requires fresh coordinator assignment before container CLI use.

**U:** Synthetic arithmetic only. No calibration, hypothesis completeness, safety, or operational-benefit claim. Raw and audit SHA256 are in `SHA256SUMS`; frozen code/gates are in `FREEZE.json`.

## Local CI

```sh
python3 -B -m pytest -q test_policies.py  # 6 passed
python3 -B -m py_compile model.py oracle.py runner.py audit.py test_policies.py
git diff --check
```
