# Post-preflight keymap race v1 — retained negative result

**Result ID:** `text-post-preflight-keymap-race-v1-20260916-01`  
**Source/plan freeze:** `ede5991327ff6cb067d12affa151ae03e3f34fb7`  
**Formal reruns:** 0

## Disposition

**PASS_NEGATIVE_TOCTOU_REPRODUCTION / FAIL_FINAL_KEYMAP_RECHECK_AS_ATOMIC_GUARD / HOLD_FIX_SELECTION**.

The fixed three-case private-X11 fault matrix passed its negative-result gates. The retained whole-payload `deliver()` is unchanged. It reads and fingerprints the US map, compiles `@`, performs its final map recheck, and then proceeds to XTest input. The experiment interposes only the first XTest call: in changed cases a separate X client synchronously installs a German or French projected map, records mutation completion, then forwards the original first event.

| case | mutation relative to first input | executor receipt | application effect |
|---|---|---|---|
| US control | none | accepted, 4 emissions | exact `@` |
| late US→German | mutation completed before first forwarded input | accepted, 4 emissions | wrong `"` |
| late US→French | mutation completed before first forwarded input | accepted, 4 emissions | wrong `2` |

In both changed cases `mutation_done_ns <= first_forward_ns`, the target-map hash observed by the mutating client equals the final map hash, and the executor still reports `accepted=true`, `error=null`. Physical input ends empty and release verification succeeds.

## Meaning

The prior route-freshness experiment proved that re-preflighting the current map at execution prevents a map change that happened **before** that check. This result closes the next boundary: a check immediately before input is still not an atomic authorization if the environment can change between that check and the first input event.

Therefore a keymap fingerprint is evidence for a state at a time, not a durable input authority. Adding yet another earlier read cannot close this class of race. A product mechanism would need actual serialization/atomicity within the relevant mutation domain, or must explicitly retain this residual risk. This experiment deliberately does not select such a mechanism because a separate X11 server-grab serialization lane already studies that class of fix and its limits.

## Evidence closure

- frozen source readback: 9/9 exact;
- static tests: 2/2 PASS;
- formal matrix exit 0, no case reruns;
- independent audit passes all predeclared timing/effect/map/release checks;
- aggregate SHA-256 `63a490fe53a1c7c29932e5891dccb8f3b28eb7cc8f8fa306087a01cbacb5049c`;
- exact aggregate retained as deterministic gzip/base64;
- no model/provider/network calls.

The outer tool display appended the known `TERM environment variable not set` after child completion. Internal receipts are exit 0; the formal result ID was not rerun.

## Limits

This is deterministic fault injection, not a natural-race frequency estimate. Private Xvfb/Tk, Group1 level0/1 projection only. The wrapper is intentionally adversarial and not a product path. No full XKB/IME, Office, Wayland, Windows/macOS, native runtime, token-efficiency or fix-efficacy claim.
