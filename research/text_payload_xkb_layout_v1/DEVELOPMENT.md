# Development / source-closure notes

1. Direct `setxkbmap -display <private-Xvfb> -layout de|fr|us -variant dvorak` returned exit 0 in this container but `setxkbmap -query` and the core keyboard mapping stayed US. That path was rejected as a layout-transfer discriminator before formal execution.
2. The retained design resolves standard XKB definitions with `setxkbmap -print` + `xkbcomp -xkb`, then projects Group1 levels 0/1 into the real private X server core mapping using `XChangeKeyboardMapping`. This is intentionally narrower than full XKB semantics.
3. Development projected matrix: US 95 accepted / 0 rejected / 0 failures; US-Dvorak 91 / 4 / 0; German 85 / 10 / 0; French 85 / 10 / 0. These are calibration only.
4. Initial Git source freeze `78e433c332ad2c5f6607494db96ebfa8a898a8d9` was **not executed formally**. Source review found the plan's non-US `mapping_changed` hard gate was reported but not included in `passed`. The runner was repaired before formal allocation; no result ID had been consumed.
