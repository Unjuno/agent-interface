# Astra ROI change-alarm threshold sweep A02

This exploratory posthoc analysis tests whether A01's generic red-mask XOR alarm can uniquely select its manually inspected frame-311 transition on the same retained video. It does not run a game, model, GUI, or input. It consumes no live allocation and makes no classification of the other detected changes.

The A01 input contains 780 ordered measurements at 0.2 source-second spacing. In frames 0-220 the largest adjacent mask change is 29 pixels; frame 311 changes by 471 pixels. Across every integer threshold from 30 through 470 pixels (the full range that is above that stable baseline and still detects frame 311), no threshold yields a single change episode. The best case has six episodes. The A01 threshold of 60 pixels has 30 separate episodes.

An episode is counted at a frame where the XOR change is strictly above the threshold and the prior frame is at or below it. The sweep is exploratory: initial PowerShell calculations preceded the saved package. The exact source CSV, source scripts, and candidate range are fixed in freeze.json; analyze.py reproduces the result and audit.py independently recomputes it using a second implementation.

## Interpretation

This is not a false-alarm rate. The other episodes may represent real health changes or other meaningful HUD changes; they are unlabelled. The result only shows that scalar pixel-change magnitude is not a unique selector for the known frame-311 event in this trace. Do not use that signal alone to authorize a policy interrupt or escalation.

The next live test still needs timestamped fresh observations during model waits and an explicit test of whether semantic state evidence changes the validity of the active local policy. If the response is observation-only, bound its cost; if it interrupts or escalates, verify release and useful effect independently.

## Reproduction

From the repository root with Python 3.10 or later, run analyze.py and then audit.py in this folder. The input samples.csv is retained in the parent A01 package and pinned by SHA-256. Both scripts use only the Python standard library.
