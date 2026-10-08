# Development findings before source freeze

These are calibration findings and are not part of the formal result counts.

1. **Ctrl+Shift+U composition rejected.** LibreOffice Writer received literal strings such as `u3b2`/`u6771`; GTK-style Unicode compose is not a generic X11 text mechanism here.
2. **Per-character Unicode KeySym remap not eligible.** It delivered many Unicode characters but exposed drops and unsafe global keyboard-map mutation.
3. **Batched KeySym remap achieved 10/10 Writer text but still rejected.** The X server `keysyms_per_keycode` structure expanded (observed 7 -> 15) and could not be restored structurally byte-for-byte even after restoring logical mappings/modifiers.
4. **UTF-8 CLIPBOARD lease succeeded in Writer development.** The multilingual corpus was exact and previous UTF-8 text could be restored, while prior owner identity was not recovered.
5. **Initial Calc clipboard attempt failed with unchanged XLSX.** This was traced to fixture mechanics: Calc requires the retained sheet acquisition coordinate and multiline paste opens a Text Import dialog before XLSX save confirmation.
6. **Corrected Calc development succeeded 10/10.** Sequence: acquire sheet -> paste -> bounded Text Import confirmation -> restore previous UTF-8 clipboard text -> save -> bounded XLSX-format confirmation. Owner identity still was not restored.

Formal design was frozen only after these candidate/mechanics questions were separated.
