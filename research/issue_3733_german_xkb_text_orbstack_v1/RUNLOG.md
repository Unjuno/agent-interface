# Run log — Issue #3733

## Formal-01 — STOP before candidate input

- Allocation: `issue3733-german-xkb-text-orbstack-formal-01`.
- Disposition: `STOP_ENVIRONMENT_OR_SETUP` (not a German text-delivery FAIL/PASS).
- The first fresh Xvfb server exposed XKEYBOARD and XTEST. Baseline was US. Exactly one `setxkbmap -layout de` returned 0; server XKB SHA changed `0e0746bf...` → `71e9bec0...`, query changed to `de`, and core keyboard map changed `23e87f0e...` → `dcfc9245...`.
- Runner then stopped at `XEV_WINDOW_ID_TIMEOUT`, before importing/constructing the candidate backend for input or sending any XTEST/key/button event. Retained `xev.log` shows its actual one-line form: `Outer window is 0x200001, inner window is 0x200002`; frozen parser incorrectly expected separate lines.
- After the audit, review of the retained row also found the pre-transition Xlib connection's `keysym_to_keycode` lookup remained cached at US levels. The next allocation therefore reconnects a fresh Xlib client after setxkbmap before checking active client-visible levels. This is a harness correction, not evidence about candidate semantics.
- Raw SHA-256: `c2de5a3851881e5935cbdba94f798b1338f0e578d021bb184ea22c808a28f6de`.
- Frozen independent audit: `STOP_ENVIRONMENT_OR_SETUP`, zero integrity errors, 17 source files and 8 raw artifact files verified, all 4/4 in-memory corruption challenges rejected.
- No rerun or raw modification. The separately preregistered successor is Issue #3756 / formal-02.

Pre-freeze construction attempts and their protocol deviation are disclosed in `CONSTRUCTION-NOTES.md`; they are not formal results.
