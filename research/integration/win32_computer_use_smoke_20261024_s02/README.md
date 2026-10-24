# Native Windows Calculator Computer Use Smoke S02

This fresh, separately frozen button-click trial followed the S01 keyboard-symbol failure. Its question was whether the visible Calculator `+` control distinguished a symbol-mapping issue from broader target-window input failure. The single returned Calculator window began at `30`; the frozen setup clicked `C`, then the test clicked `1`, `2`, `+`, `3`, `0`, and `=` once each.

**Scoped result: `PASS_BUTTON_ROUTE_TASK_EFFECT_SCOPED`.** The visible operation became `12 + 30 = 42`, and every click was followed by a new screenshot. No retry occurred. The raw final screenshot, frozen conditions, per-call receipt summary, and hashes are retained here.

Together with S01, the result is consistent with a `plus` key-symbol mapping problem in this route. It does not identify the implementation cause. This is one native-Windows Calculator smoke, not a WSLc computer-control pass, independent task-score validation, input-release proof, blocked-I/O recovery result, reliability estimate, MAP01 result, or efficiency comparison. `click_return_ms` measures only tool-call duration.
