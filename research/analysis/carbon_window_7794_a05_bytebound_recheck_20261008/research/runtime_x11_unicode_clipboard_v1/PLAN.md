# X11 Unicode clipboard lowering v1 — frozen experiment plan

## H
A UTF-8 CLIPBOARD lease can produce exact durable multilingual text in real LibreOffice Writer and Calc without mutating the X keyboard map, but it cannot transparently preserve the prior clipboard owner identity. Therefore it may justify a scoped side-effect capability, not silent promotion of generic `input.text`.

## T
Fixed formal order: **Writer, then Calc**. Each arm uses a fresh private Xvfb/Openbox display, fresh LibreOffice profile, fresh artifact, and the same fixed 10-string corpus: `café`, `βeta`, `東京`, `あいうえお`, `🙂`, `e◌́`, `naïve`, `résumé`, `中文`, `한국` (the combining example is encoded as `e` + U+0301).

A separate clipboard-owner process first owns UTF-8 text `PREVIOUS-αβ`. Before fresh execution, a stale-observation program must be refused with no owner/text change. Fresh execution acquires the editable surface, leases CLIPBOARD, pastes the payload, restores the previous UTF-8 text while the lease remains alive, saves, verifies empty physical input, and records the X keymap before/after. Calc additionally accepts the deterministic Text Import and XLSX-format dialogs. Durable artifacts are scored only after executor completion by a separate ODT/XLSX scorer.

Successor formal result ID after the retained harness failure: `x11-unicode-clipboard-v1-20260916-02`. The prior `-01` result is immutable and must not be rerun. The successor matrix invocation MUST pass an absolute `--out` path so LibreOffice profile `file://` URIs are absolute. Each arm runs once; no failure-driven replacement or rerun.

## D
`SCOPED_UNICODE_PASS` requires both apps exact, stale refusal before clipboard/input mutation, previous UTF-8 content restored while lease alive, unchanged keyboard map, and empty terminal physical input.

`GENERIC_TEXT_PROMOTION` additionally requires prior clipboard owner identity to be restored. If scoped Unicode passes but owner identity does not, disposition is `PASS_SCOPED_UNICODE_CLIPBOARD_LOWERING / REQUIRE_EXPLICIT_SIDE_EFFECT_CAPABILITY / HOLD_GENERIC_TEXT_PROMOTION`.

## C
Clipboard ownership is process-local state; restoring bytes is not restoring owner identity, TARGETS, rich MIME data, or clipboard-manager semantics. Calc has an app-specific Text Import confirmation. Focus/save/dialog behavior may vary by application/locale.

## U
Private Xvfb/Openbox only; UTF-8 clipboard text only; no full IME composition, rich clipboard fidelity, Wayland, Windows, macOS, WSLg, model/provider calls, or product-level reliability claim.
