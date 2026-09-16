# Text-delivery payload-aware routing v1 — retained formal result

**Result ID:** `text-delivery-payload-routing-v1-20260916-01`  
**Source/plan freeze:** `df9a7b68c8ee287e12e8127e7d6e20836a830d54`  
**Formal reruns:** 0

## Disposition

**PASS_PAYLOAD_AWARE_PREINPUT_ROUTING / REJECT_COARSE_ASCII_AS_ROUTE_ELIGIBILITY / HOLD_SHARED_RUNTIME_PROMOTION**.

The fixed 104-trial private-X11 matrix passed. The experiment composes the merged side-effect-aware route model with the retained whole-payload direct-key preflight and compares its decision with the old coarse `ASCII -> direct_keys` decision.

| Metric | Result |
|---|---:|
| Trials | 104/104 gate PASS |
| Payload-aware direct routes | 56 |
| Explicit clipboard routes | 24 |
| No-route / zero-input refusals | 24 |
| Coarse-selector decision mismatches | 40 |
| Candidate map invariant | 4/4 arms |
| Terminal physical input empty | 4/4 arms |

US and US-Dvorak have 0 selector mismatch. German has 20 mismatches and French has 20. Each retained nonrepresentable ASCII character contributes two mismatches: transparent budget changes coarse `direct_keys` to **no route**, and explicit clipboard budget changes coarse `direct_keys` to **`clipboard_utf8`**. This is a route-eligibility overclaim, not evidence that the retained direct executor itself injects wrong input: that executor already preflights and fails closed.

## Pre-input fallback property

All 48 non-direct trials had `direct_emissions=0`. All 24 clipboard trials therefore chose clipboard before any direct-key input. Every clipboard trial produced exact application text, exactly one clipboard mutation-version increment, four paste key events, unchanged applied keymap, and empty physical input afterwards. Clipboard ownership changes are deliberate side effects covered by the explicit request budget; this route is not transparent text.

All 24 no-route trials produced zero direct input, zero paste input, zero application text, and no clipboard mutation. This includes transparent Unicode plus German/French layout gaps.

## Concrete retained mismatches

German coarse ASCII routing overclaims direct-key eligibility for `@[\]^` + backtick + `{|}~`. French overclaims `#@[\]^` + backtick + `{|}`. Under an explicit clipboard budget, payload-aware routing selects clipboard for those gaps; without that budget it refuses before input. `office` remains direct on all four layouts. `βeta` remains no-route when transparent and clipboard when the clipboard side-effect budget is explicit.

## Evidence closure

- 14/14 source blobs matched the GitHub freeze before formal execution;
- exact dependency blobs: coarse model `6ed3fccd...`, direct preflight `35c7375e...`;
- deterministic unit/static tests: 10/10 PASS;
- matrix exit 0; aggregate SHA-256 `92e2541391714e5e241c30761c1e91126fd9facdc39a208ae94f8a29d20ac378`;
- read-only audit rechecked all 104 trials, route-specific emission invariants, clipboard versions, semantic effect, keymap and physical release;
- exact aggregate is reconstructible from `aggregate.json.gz.b64`;
- no model/provider/network calls.

The outer tool display appended the known `TERM environment variable not set` after child completion. Internal unit and matrix receipts are both exit 0; the result ID was not rerun.

## Architectural implication

A route manifest can say that a backend has a **candidate direct-key mechanism**, but dispatch eligibility must be evaluated against the concrete payload and current keymap before input. `ASCII=true` is not sufficient route eligibility. If direct preflight fails, fallback is a fresh route decision using the caller's declared side-effect budget; it is not an automatic retry after partial direct input.

## Limits

This remains a Research Preview integration fixture: private Xvfb/Tk, standard XKB definitions projected to Group1 level0/1, not full XKB. AltGr, extra groups, dead keys/compose, IME, Office, Wayland, Windows/macOS, native runtime integration and provider/model-token effects are unproven. Clipboard ownership mutation is intentionally not restored or hidden.
