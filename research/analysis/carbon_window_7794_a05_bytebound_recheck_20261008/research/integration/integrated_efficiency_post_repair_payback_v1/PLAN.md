# Integrated post-repair reuse payback v1

Task: INTEGRATED-EFFICIENCY-POST-REPAIR-PAYBACK-20260917-001
Issue: #967
Publication base: 83e1168b4175e32342e975e9950afa1eba81bc6b
Authoritative ledger blob: 7db368b2d492b5b95f5f038fb7cb5dd6b78a27a7

H: Over the actually retained task4-task6 post-invalidation horizon, persistent repair + repeat_B reuse has lower wall/model-side work than ephemeral cold/nonpersistent task4-task6, while any local-work increase remains explicit.

T: Deterministic stdlib-only reconstruction from the exact retained phase ledger. Compare only layout_change + repeat_B for persistent and ephemeral. Compute same-unit sums/differences/ratios. Keep cached input subset-only. One formal invocation after source-first remote freeze, reruns 0.

D: PASS only if source/phase identities are exact, persistent horizon wall/input/output/reasoning/generations/images are all lower, persistent repeat_B model fields are exactly zero, local work remains separate, and independent audit/corruption controls pass. HOLD if same-unit payback does not hold. Source/phase/unit substitution is FAIL_INTEGRITY.

C: different-arm descriptive comparison; no same-arm causal claim. Task5-6 may favor reuse.

U: one retained Chromium allocation, one layout change, two observed post-repair reuse tasks; no extrapolation beyond task6.
