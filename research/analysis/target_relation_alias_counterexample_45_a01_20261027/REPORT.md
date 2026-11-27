# A01 — relation-signature alias counterexample

**Disposition: synthetic identifiability counterexample; no live claim.** Source `050b792652b678f1d75986ac448525f33dfe9190`, prototype SHA-256 `ab4ceda4e707d3d4d2e3de95c0383c47e9b762b77f8ef0ae30278fbd257da449`. The four deliberately authored worlds and their hidden original-target labels were frozen before the single offline run.

Two pairs have identical matcher-visible observations but different stipulated original targets. In all four, the #8777 matcher returns `REVALIDATED`, candidate index 0, `authority=none`; this is wrong under the hidden labels in the swapped and replaced worlds. The labels are synthetic oracle assumptions, not facts observed in an application, and 2/4 is not a prevalence estimate. No deterministic method restricted to the same observations can distinguish each paired world.

A comparison policy abstaining when multiple same-surface/container/role/label candidates exist returns UNKNOWN for both two-candidate worlds, avoiding the stipulated swapped rebind at the cost of rejecting the stable case. It still selects the single replacement because the single-candidate worlds have identical visible data. An additional trustworthy identity witness or explicit re-grounding is therefore required to distinguish these synthetic worlds; the conservative policy alone does not establish semantic identity.

The independent check in `audit.py` verifies the frozen input hashes, identical visible pairs, divergent labels, outputs, authority and counterexample classification. This does not regrade #8777's construction result or #8675's separately scoped synthetic corpus; whether those corpora contain these cases has not been established. No UI, runtime dispatch, external allocation, WSLc, Docker, model or physical input was used.

A second auditor, `audit-v2.py`, independently recomputes matcher choices and scores from the frozen input rows; all eight checks pass.
