# Run log — Issue #3764

## Formal-01 — STOP before German transition

- Allocation: `issue3733-german-xkb-map-diagnostic-formal-01`, frozen at commit `d244ebb6abfa2208616f0cc61535f5e264e18deb`.
- Both fresh Xvfb servers started with XKEYBOARD/XTEST. The first requested German row captured US baseline query and xkbcomp dump, then stopped before `setxkbmap` because the pinned image does not contain `xmodmap` (`FileNotFoundError`). The US control row reached the same missing-tool STOP. No candidate code or XTEST event ran.
- Raw SHA-256: `662bbce75026f7ddfd5dbcb11dd396451598421f7aa3b256eae8face840dbaea`.
- Independent audit disposition: `STOP_DIAGNOSTIC`; zero integrity errors; 6 existing artifact files checked. Findings (`german_row`, `control_row`, `selected_symbols_unchanged`, `raw_capture_missing`) correctly prevent a diagnostic PASS. The audit independently confirms this allocation did not resolve the server/client map discrepancy.
- No retry. Next successor should use only tools confirmed in the image and compare the `xkbcomp` server map with Xlib core-map reads; do not attempt package installation or candidate input.

## Formal-02 — STOP; layout command returned success but server stayed US

- Allocation: `issue3733-german-xkb-map-diagnostic-formal-02`, frozen at commit `76e7f2b5a2da2ee3149c94a400c60474bbb68cac`.
- The German row started fresh Xvfb with XKEYBOARD/XTEST. Baseline query and xkbcomp dump were US. Exactly one `setxkbmap -layout de` returned 0 with empty stdout/stderr, but immediate `setxkbmap -query` still reported US; xkbcomp and fresh-Xlib maps were byte-equivalent to baseline. Runner stopped before claiming a layout transition. US control row was not run after the first-row stop. No candidate or XTEST input ran.
- Raw SHA-256: `0bea5aa9c6a9d2437ba7f25bb51193b6852d662361919538c1c821cf916f418d`.
- Independent audit: `STOP_DIAGNOSTIC`, 0 integrity errors, 8 artifact files checked, finding `row_schedule` because a valid early STOP correctly prevented the control row. No artifact or Xlib snapshot mismatch was found. This formal observation differs from formal-02 of Issue #3733, where query/dump reported German. Do not reconcile them into a single outcome.
- Next step requires a new successor allocation to capture explicit target display and verbose rules/compiler selection, determine why a success return can leave the server US, and keep its logfile and output manifests one-shot.
