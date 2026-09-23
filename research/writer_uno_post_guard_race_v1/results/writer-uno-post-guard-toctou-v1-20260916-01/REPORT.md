# Writer UNO post-guard TOCTOU v1 — retained negative result

**Result ID:** `writer-uno-post-guard-toctou-v1-20260916-01`  
**Source/plan freeze:** `519482c40b2fed85faa5d0b315c4a52e1602ca43`

## Disposition

**RETAIN_POST_GUARD_TOCTOU_BOUNDARY / FAIL_ATOMIC_RECOVERY_CLAIM / HOLD_FIX_SELECTION**.

Nine fresh private Xvfb/Openbox/LibreOffice Writer sessions executed once: no-fault, post-guard focus switch, and post-guard target-text mutation, each repeated three times. Every session first passed exact URL+RuntimeUID+text+age and active/focus XID guards. Fault hooks, when present, were then executed strictly after the guard receipt and before the first XTest input.

| condition | sessions | retained outcome |
|---|---:|---|
| none | 3 | 3/3 A=`bookkeeperoffice`, B=`bookk` |
| focus after guard | 3 | 3/3 A=`book`, B=`bookkkeeperoffice` |
| text mutation after guard | 3 | 3/3 A=`booxkeeperoffice`, B=`bookk` |

All 9 sessions record `guard_completed_ns < first_input_ns`; all 6 injected sessions record `guard_completed_ns < fault_injected_ns < first_input_ns`. All physical input is empty at termination. Median guard-to-first-input intervals were 2414 ns (no fault), 173301534 ns (focus hook), and 121787214 ns (text hook). The injected hooks intentionally widen the gap and do not estimate natural race frequency.

## Interpretation

The retained PR #280 guards are necessary but not an atomic commit boundary. A document/window state transition scheduled after the final proof can still redirect or invalidate subsequent input. Adding another pre-input check can move the race boundary but does not, by itself, prove atomicity.

This result does not select a fix. X server serialization may address only X-side focus changes and not application-internal UNO text mutation; application-side atomic editing may change the delivery semantics. Those are separate mechanisms requiring evidence.

## Evidence closure

- source readback 6/6 exact before formal execution;
- Python compile check PASS;
- 9/9 formal arms completed once, exit 0, predeclared gate PASS;
- all 9 release receipts empty;
- no model/provider/network calls; formal arm reruns 0;
- canonical raw rows 7,793 bytes, SHA-256 `978c63659bb57de4f28343980eeb585deed8adc5eed0e51a65cad4f68d07a02b`.

## Limits

This is a deterministic existence test, not a race-rate estimate. It is private Xvfb/Openbox/Writer only and intentionally inserts a fault hook. No Wayland/Windows/macOS/Office-general/IME/model-token claim.
