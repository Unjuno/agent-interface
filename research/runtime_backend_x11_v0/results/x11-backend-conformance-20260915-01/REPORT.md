# X11 backend conformance v0 — retained first result

**Result ID:** `x11-backend-conformance-20260915-01`  
**Source freeze:** `cfa5b01e5df8351fdd51672904aabf0e35d8f9a1`  
**Portable contract dependency:** `0f2bda3c7d9eb863714795789dcfa2ea9fe86bd5` (PR #97 head)

## Disposition

**PASS_PRIVATE_X11_BACKEND_CONFORMANCE / HOLD_PRODUCT_PROMOTION**.

The source-frozen private Xvfb/XTEST/Xlib run passed its scoped contract/effect/release gates. This is a real backend mechanics result, not a promoted runtime, office-app benchmark, or evidence for Windows/macOS/Wayland.

## Retained checks

- unit suite exit: 0;
- private runner exit: 0;
- 64/64 seeded stress programs admitted and ended with verified empty tracked physical input;
- stale observation, stale binding and expired lease each emitted **zero** backend input and zero fixture events;
- primary valid program independently delivered focus, pointer motion, left click at window-client `(40,50)`, text `office`, Ctrl+S, scroll-up, one capture and terminal release;
- exact valid-effect scorer: PASS;
- all release receipts: PASS (`keys_down=[]`, `buttons_down=[]`);
- initial/final captured pixel SHA-256 differs after delivered fixture effects;
- fixture retained 221 non-Expose events, including 76 key/button press effects.

The local X11 geometry translation initially failed during construction because `TranslateCoords` direction was reversed, producing `(-80,-90)` instead of `(80,90)`. That was a development calibration failure before source freeze. The frozen implementation uses the corrected direction and the retained result reports `(80,90,360,240)`.

## Evidence boundaries

The backend never reads the fixture event ledger during execution. Admission comes from the portable contract oracle; XTEST emission, fixture-received events, capture bytes and release-state verification are logged separately.

The fixture is synthetic and runs on private Xvfb. XTEST acceptance does not establish arbitrary application semantic completion, WSLg behavior, Wayland behavior, native Windows/macOS support, Unicode/IME completeness, accessibility integration, or provider-token efficiency.

Text in this v0 adapter intentionally supports a strict ASCII subset. Rich text/IME semantics must be a separately declared capability rather than guessed.

## Container wrapper anomaly

After the retained child run completed, the outer container command wrapper returned status 1 with `TERM environment variable not set`. The retained internal receipts are unambiguous: `unittest.exitcode=0`, `runner.exitcode=0`, nested experiment exit `0`, report `passed=true`, and all retained SHA-256 manifest entries verify. The result ID was **not rerun**.

## H/T/D/C/U

**H:** one real X11 backend can implement the portable contract without adding X11 semantics to the semantic program.  
**T:** source-frozen private Xvfb/XTEST/Xlib fixture; primary exact-effect case + three zero-input rejection cases + held release + 64 seeded stress cases.  
**D:** PASS for this private X11 mechanics scope; HOLD for product/native-platform promotion.  
**C:** compositor/window-manager behavior, layout/IME, real office apps, observation races and permission systems may expose missing backend semantics.  
**U:** Xvfb only; diagnostic timing uncontrolled; no model/provider calls; no Wayland/Windows/macOS execution.

## Successor

Integrate this adapter only after PR #97 contract disposition. Next useful experiments are (a) the same backend contract against one real desktop/office fixture with independent semantic scoring, and (b) a separate Wayland capability/portal experiment. Do not infer either from this result.
