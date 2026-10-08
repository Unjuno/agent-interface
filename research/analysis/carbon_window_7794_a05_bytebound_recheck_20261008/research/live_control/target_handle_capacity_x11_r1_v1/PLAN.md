# #1704 plan — live X11 target-handle capacity 1 vs 2

TASK: `TARGET-HANDLE-CAPACITY-X11-R1-20260918-001`
BASE: `4072b25c7510e8fb285ad34584fc9bdb1f46fa6d`
Parents: #1682 / PR #1700; #45. Related: #1668.

## H
On a stable private X11 surface with request sequence A,B,A,B, retaining two fresh semantic handles reduces full-frame re-grounding scans from four to two while preserving click correctness. Replacing the surface before access 3 changes the current X11 surface identity; retained old-surface handles must become ineligible, so both capacity 1 and capacity 2 require four full groundings.

## T
One source-frozen 20-session block: capacity {1,2} × surface {stable,replace-before-third-access} × 5 fresh sessions. Every action begins with an exact current X11 RGB capture and actual X input-focus readback. Cached handles are resolved by the exact vendored `TargetHandleStore`; only VALID/REVALIDATED points may be clicked. Cache miss or invalidity invokes a full-frame exact-pattern grounding scan and fresh mint. XTEST performs one click. The Tk fixture writes an independent click ledger that the controller reads only after all four actions.

## D
PASS scoped iff all 20 sessions complete with A,B,A,B and zero wrong clicks; stable k1 has G=4/session, stable k2 G=2/session; replace has G=4/session for both capacities; every retained old-handle probe after replacement is ineligible SCOPE_MISMATCH; terminal button neutral in every session; independent audit and corruption controls pass.

## C
Local handle validation itself can cost as much as grounding; stable semantic IDs/APIs can subsume image grounding; surface replacement is stronger than same-surface semantic invalidation; visible multi-cursors are not required; model/token savings require avoided full grounding to have crossed a model boundary.

## U
Private Xvfb/Tk only; no model/provider/network/user desktop/user data. Counts are dimensionless. Timings are descriptive only and not promotion gates. No token, end-to-end latency, Wayland, production, or cross-app claim.
