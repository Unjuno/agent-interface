# Post-measurement metadata note

The frozen `run_case.py` writes the literal result field
`task = INKSCAPE-ATSPI-LAUNCHER-BUS-PATH-LIFETIME-CONSTRUCTION`.
That string was carried unchanged into the six formal first `result.json` files.

This is a retained metadata anomaly, not a reason to rewrite the measured rows. The formal allocation identity is `INKSCAPE-ATSPI-LAUNCHER-BUS-PATH-LIFETIME-20260916-027`, frozen in Issue #488 and `prereg.json`, with the measured runner bound by SHA-256 `4ea1379b410374edcb4cd53c8f3f240326ad186885f6918b43bee03745b6ff76`.

The frozen audit does not use the stale `task` literal as a gate. It validates the six-case schedule/arm, completion, Registry ownership, A/B path continuity, old-path names, final keymap state, and the launcher PID-attribution boundary. Raw outcomes and their hashes remain unchanged.

Do not edit the historical `result.json` files to cosmetically repair this string. A future allocation should give the runner an explicit allocation ID before source freeze.
