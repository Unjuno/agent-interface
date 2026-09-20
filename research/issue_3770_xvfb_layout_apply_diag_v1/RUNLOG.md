# Run log — Issue #3770

## Formal-01 — STOP; Xvfb remained US despite successful rules resolution

- Allocation `issue3733-german-xkb-apply-diagnostic-formal-01`, frozen at `d0fbd1f3c2566aa6b09a2227f2a291218e84cd11`.
- Fresh Xvfb :181 exposed XKEYBOARD/XTEST; US baseline captured. Explicit `setxkbmap -display :181 -verbose 10 -layout de` returned 0. Its retained verbose output resolved `evdev`, `pc105`, `layout: de`, `evdev+aliases(qwertz)`, `pc+de+inet(evdev)`. `setxkbmap -print -verbose 10 -layout de` also emitted the expected German keymap.
- Despite that, delayed `setxkbmap -display :181 -query` remained US; server xkbcomp and fresh Xlib map were unchanged. Runner STOPPED after the first row; no US control row, candidate, or XTEST event ran.
- Raw SHA-256: `bdae58feeb780458cde39b9b4822c19e656c3ffd42270dcfa9190cad4c2ad7df`.
- Independent audit: `STOP_DIAGNOSTIC`, zero integrity errors, 10 artifact files checked; findings `layout_unresolved`, `server_dump_not_changed`.
- This establishes a repeatable separation between successful map/rules construction and server-applied map state for this formal run, but not the root cause. No retry. A successor may test explicit `xkbcomp` application of the generated map, then verify the server state independently.
