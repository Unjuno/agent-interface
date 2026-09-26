# Preserved predecessor STOP — Issue #3792 formal-02

This is an unchanged copy of the first row and host logs from the one-shot formal-02 allocation. It is retained here so the succeeding Issue #3794 result package preserves the harness failure that motivated the corrected successor. It is not a candidate result and it is not part of the #3794 formal matrix.

- Frozen preregistration commit: `12c1730aa87ae7fda962ae58f0184d586ca88dc3` on branch `research/issue-3792-german-xkb-formal02-20260921`.
- Reached phase: `receiver_focused`; InputOnly window mapped/focused and XKEYBOARD/XTEST available.
- STOP: XLookupString helper raised `KeyError:'DISPLAY'`; parent then raised `AttributeError` because `run_row()` returned `None` after `finally`. No map transition, preflight, or candidate formula test was reached. This is solely a harness STOP.
- Formal invocation host stdout SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty).
- Formal invocation host stderr SHA-256: `395e9f573b77e221278a490be0007dcf819f743fb4b2c1c74864833491d46fab`.
- Partial row SHA-256: `9b875a1c99e5a99000f3729c7f3e5a27f5f4f85d33be52a4262f01d50b246782`.
- Xvfb log SHA-256: `f172a1b0f5cf2a0d462c51dfc335af1a1dfc8e873cb66f61d018c8b1b35fe416`.

No retry or patch was made to formal-02. The corrected formal-01 under #3794 is a distinct allocation.
