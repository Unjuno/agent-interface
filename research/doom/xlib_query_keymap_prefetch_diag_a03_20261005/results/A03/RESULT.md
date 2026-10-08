# A03 result — STOP

The frozen candidate ran once after successful setup (Ubuntu 24.04.5 arm64, Python 3.12.3, Python-Xlib 0.33-2, Xvfb 21.1.12-1ubuntu1.8) and exited 1 with `AttributeError('detail')` before appending either edge. The raw trace has no edge receipts. The raw-only auditor was not run; runner status records auditor exit 125. Xvfb stopped normally with exit 0. The guest is stopped and retained.

This STOP does not establish that query-keymap prefetch occurred or that the input events were undelivered. One plausible cause is an unrelated queued event whose Xlib representation lacks a `detail` property; the candidate did not retain the event type, so that cause is unverified. No retry was made.

This remains a Python-Xlib/Xvfb diagnostic only. It does not establish what A03's prior client-event queue contained and does not measure game input, model behavior, task feedback, threat response, recovery, or MAP01.
