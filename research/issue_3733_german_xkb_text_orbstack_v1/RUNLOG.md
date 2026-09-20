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

## Formal-02 — STOP before candidate input; audit integrity failure

- Allocation: `issue3733-german-xkb-text-orbstack-formal-02`, frozen at commit `1f3ae4f212b71ae15768a24394364c8585a8c9cc`; source base `76965311d899815174b5ed081ff439bd4533ef63`; candidate blob unchanged at `9cae101a219348077668c8fc086acf8e13154afe`.
- The pinned OrbStack container started a fresh Xvfb and observed XKEYBOARD/XTEST, US baseline, and one successful `setxkbmap -layout de`. The server dump/query changed to German, but the fresh client's full core-map fingerprint remained identical to the US baseline (`23e87f0e...`), so the runner correctly stopped at `STOP_SETUP_BLOCKED_NATIVE_XKB_APPLY` before constructing/invoking the candidate. No xev receiver, candidate plan, or XTEST event exists.
- Formal raw SHA-256: `d782263b780d848c5cc1b3735047649074c65636f4515017c895f0546d4fa97f`. The first formal Docker invocation did run and produced this raw; afterward zsh rejected assignment to its reserved `status` variable, obscuring the command's exit code. A subsequent attempted launch was rejected because formal-02 output already existed; that retry log overwrote the first invocation's host log. The retained `formal-02.container.log` is therefore evidence of the rejected repeat only, not the formal run. Raw and individual map artifacts govern the scientific disposition.
- Independent audit: `FAIL_AUDIT_INTEGRITY`, 0 candidate findings, 17 source files and 7 extant artifact files checked. The runner hashed its transient `raw.partial.json` into the final artifact inventory and then deleted it, producing `artifact_inventory`. Audit raw SHA is the same `d782263b...`; audit log is retained. This audit failure does not erase the row-level setup STOP and does not permit a PASS.
- Formal-02 is closed as an immutable STOP/audit-failure record. Do not rerun or alter its raw. Issue #3756 records the predecessor implementation defects; a fresh successor is required to fix both the German map-verification question and artifact accounting.
