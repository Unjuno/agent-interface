# A2 mixed-app guarded recovery — policy-independent Chromium shortcut task effects

Task: `MULTI-APP-GUARDED-RECOVERY-A2-20260918-002`, Issue #1728.

H: geometry, focus, window-binding and current-observation staleness each refuse before task input; after explicit refresh/rebind, a universal Chromium keyboard shortcut on the independently active intended top-level produces the expected task effect.

T: private Xvfb/Openbox + Chromium + XTerm + Python-Xlib/XTEST. Preserve #1711's four perturbations and gates. Change only blocked file-URL task effects to built-in `Ctrl+J`/`Ctrl+H` transitions with exact `_NET_WM_NAME` scoring. Construction excluded. Formal: four fresh sessions exactly once.

D: PASS only if every formal session emits GEOMETRY/FOCUS/BINDING/OBSERVATION refusals in order with zero task-input increase at refusal; has four fallback batches with active-window match; exact Downloads/History/Downloads/History effects; old/new Chromium IDs differ and old is gone; terminal input neutral; formal1/reruns0/replacements0/tuning0; audit/integrity pass.

C: internal Chromium pages are narrow deterministic task effects; WM activation is an explicit recovery primitive; no performance or arbitrary semantic-recovery claim.

U: Linux private-X11/container only; no model/provider/network/token/human-tempo/cross-backend claim. #1711 remains an immutable setup stop.
