# Native Windows Calculator Computer Use Smoke S01

This exploratory live UI smoke froze one harmless `12 + 30 = 42` task through the supported `@oai/sky` window-specific keyboard route. The target was the single returned Microsoft Calculator window, initially in Standard mode at `0`.

Result: **FAIL_TASK_EFFECT**. All six targeted key calls returned and each action was followed by a fresh screenshot, but the `plus` action yielded a visible `12 =` operation line; the final display was `30`, not `42`. No retry was sent. The final screenshot and per-call receipt summary are retained alongside the pre-input conditions.

This finding is specific to one window and one `plus` key symbol. It does not establish the exact mapping cause, key-up state, input release, blocked-I/O recovery, application reliability, WSLc behavior, MAP01, or efficiency. A fresh button-click trial is the next discriminating check.
