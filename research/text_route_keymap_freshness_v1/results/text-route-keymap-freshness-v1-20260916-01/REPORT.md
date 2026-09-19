# Text route keymap freshness v1 — retained formal result

**Result ID:** `text-route-keymap-freshness-v1-20260916-01`  
**Source/plan freeze:** `57cb5f39dc1dacd4da6f590832b200d8a3025324`  
**Formal reruns:** 0

## Disposition

**PASS_EXECUTION_TIME_KEYMAP_FRESHNESS / REJECT_ROUTE_SELECTION_AS_AUTHORITY / REQUIRE_FRESH_RESELECTION_FOR_FALLBACK / HOLD_SHARED_RUNTIME_PROMOTION**.

The fixed three-case private-X11 matrix passed. A direct-key plan for `@` was selected and compiled under the US map; before first input the target map was either left US or changed to projected German/French. The experiment compares a deliberately unsafe stale compiled plan with the retained execution-time whole-payload preflight and then performs fresh route reselection.

| transition | stale compiled plan effect | execution-time preflight | fresh transparent | fresh clipboard budget |
|---|---|---|---|---|
| US→US | `@` | direct exact `@` | `direct_keys` | `direct_keys` |
| US→German | `"` | zero-input `TEXT_NOT_REPRESENTABLE_IN_KEYMAP` | no route | `clipboard_utf8` -> exact `@` |
| US→French | `2` | zero-input `TEXT_NOT_REPRESENTABLE_IN_KEYMAP` | no route | `clipboard_utf8` -> exact `@` |

The German/French stale-plan controls each emitted four key events and produced a wrong application effect. The retained executor, which rebuilds the whole-payload plan from the **current** map immediately before execution, emitted zero events in both changed-map cases.

## Fresh fallback boundary

After safe refusal, fallback was not inherited from the earlier route decision. Routing was recomputed against the changed map:

- transparent budget -> no route, no input;
- explicit clipboard-content/owner/TARGETS budget -> `clipboard_utf8`;
- clipboard actuation then produced exact `@`, one mutation-version increment and four Ctrl+V events;
- applied target map remained invariant and physical input ended empty.

This separates three moments that must not be collapsed: semantic text intent, route eligibility at selection time, and execution authority under the current environment.

## Evidence closure

- 12/12 frozen source blobs matched before formal execution;
- static tests passed 2/2;
- formal matrix exit 0, no case reruns;
- independent read-only audit: 21/21 checks PASS;
- aggregate SHA-256 `a429cc57d974e9ebfc156cd809c2342f929668f9661c3b1468a5726576614194`;
- exact aggregate is reconstructible from deterministic gzip/base64;
- no model/provider/network calls.

The outer tool display appended the known `TERM environment variable not set` after child completion. Internal unit/matrix receipts are exit 0; the result ID was not rerun.

## Architectural implication

A route-selection result must not be treated as a durable permission to inject input. Environment-dependent routes need an execution-time validity proof. If that proof fails before input, the operation must stop with zero input; any alternate route requires a new decision against the current environment and the original caller side-effect budget.

This is the same structural separation already seen in observation freshness and target binding: **selection is not authority; current binding is part of admission**.

## Limits

Private Xvfb/Tk with standard XKB definitions projected to Group1 level0/1. The stale-plan arm is an intentionally unsafe negative control, not a proposed API. This does not prove full XKB/AltGr/dead-key/compose/IME semantics, Office transfer, Wayland, Windows/macOS, native-runtime integration, provider/model token effects, or atomicity after input begins.
