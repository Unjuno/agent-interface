# Issue #4189 — MAP01 expiry release bound

Retained-artifact measurement successor to #3243. Historical run 35471098475 and its FAIL remain immutable.

H: in the exact one-key recovery fixture, a verified neutral owner expiry with matching lease deadline can provide a censored key-up interval when it occurs before a later redundant ordinary-up attempt whose owner transition is false.

T: artifact 10592963131 only; source-bound InputOwner v10 semantics; pair1/2/3 recovery arms; exact interval-union reconstruction; independent raw auditor; corruption controls. No new ViZDoom/X11/model/input allocation.

D: PASS only if pair1 is unchanged with zero substitution, pair2/3 each use exactly one strictly gated expiry substitution and become internally valid, audit mismatch0, corruption controls reject, and the historical #3243 summary remains untouched.

C: single key, single owner, matched valid_until and neutral expiry only. No generic repair of unverified releases.

U: measurement evidence only; no recovery efficacy or task-effect claim.
