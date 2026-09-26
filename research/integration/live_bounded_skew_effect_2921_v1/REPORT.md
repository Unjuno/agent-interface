# Issue #2921 — bounded-skew join live application transfer

## Disposition

**HOLD_LIVE_TRANSFER_UNSAFE_REPLACEMENT_ALIAS / STOP_BEFORE_FORMAL**

The planned formal allocation was not started. Construction on a real xterm/X11 application exposed a preregistered unsafe replacement join under the unchanged #1594 identity contract.

## H

The exact #1594 2 ms bounded-skew rule should retain stable/delayed-render observations while failing closed on focus change, application/window replacement and identity mismatch before task input. Where a join is authorized, an independent application effect is scored from a private file unavailable to the join implementation.

## T

Private Xvfb/Openbox/xterm. The exact current-main #1594 `candidate` and `strict` functions are copied byte-for-byte in `join_rule_1594.py`; source Git blob at claim was `eb73d42e89e9ea2b5851c4b95dc169aed8417f8b`. Fixed budget 2,000,000 ns. Two policies and six schedules were exercised once each in construction-04 (12 fresh xterm sessions): STABLE, DELAYED_RENDER, FOCUS_CHANGE, WINDOW_REPLACEMENT, IDENTITY_MISMATCH, EFFECT_TRANSITION. Join code never reads the private effect file; a separate scorer does. Unsafe schedules never receive task input.

## D / first valid construction gate

Independent raw audit reconstructs 12/12 rows with errors=[] and 13/13 coherent corruption controls rejected.

The bounded-skew policy correctly joins STABLE, DELAYED_RENDER and EFFECT_TRANSITION and obtains exact private-file effects. It refuses FOCUS_CHANGE and IDENTITY_MISMATCH. However, WINDOW_REPLACEMENT is incorrectly joined:

- initial xterm PID 8520; replacement PID 8537;
- initial/current XID both 4194316;
- geometry remains `[0,0,640,360,0,24]` and focus resolves to the recycled XID;
- caller-visible `(session,surface,generation)` remains coherent;
- unchanged #1594 candidate says JOIN=true;
- scorer-only application lifetime says replacement, so independent oracle=false;
- task input is disabled on this construction schedule; effect remains ABSENT.

This fails the Issue's required construction property before formal. The 2 ms threshold and join rule were not tuned. The distinct lifecycle-token repair is owned by Issue #4197 and is not duplicated here.

## C

OS process lifetime is scoring truth for this controlled replacement, not a general application identity API. The counterexample establishes that XID/session/generation as authored here is insufficient under same-XID reincarnation; it does not establish that PID should be the production fix. The strict exact-anchor comparator is intentionally over-conservative.

## U

No model/token/human-tempo claim, no general GUI reliability, no Wayland/remote X11, no production authority, no natural replacement rate, and no net-latency benefit measurement. Formal denominator remains unconsumed because the preregistered replacement gate already failed in construction.
