# A5 — X11 temporal capture cadence 10 Hz

Issue #1065. BASE `3c34e3cea2a39e961e097b41444ff4a7563a4170`.

H: with all A4 mechanics fixed, reducing only capture cadence from 20 Hz to 10 Hz will remove A4's overhead-gate violations if cadence pressure is causal.

T: private Xvfb/Tk 320x240; baseline no capture vs raw full-frame XGetImage at 10 Hz with 500 ms bounded raw ring; 300 ms warmup; 1500 ms measured; six fresh counterbalanced pairs; one formal invocation; no reruns/replacements/tuning.

D: PASS_X11_TEMPORAL_CAPTURE_10HZ_SCOPED iff capture>=12/arm, exceptions0, drops<=1, capture p95<10 ms, CPU<0.20, ring<=7 frames, paired median fixture-count ratio in [0.97,1.03], paired median p95-gap increase<=2 ms, and candidate max-gap excess<=10 ms for every pair. HOLD only if >=2 baseline max gaps>100 ms. Otherwise REJECT_CAPTURE_COST_AT_10HZ.

C: A4's pair5 may have been unrelated host scheduling noise; a similar outlier may recur at 10 Hz.

U: Xvfb/Tk/python-xlib, 320x240 raw only; no real compositor, encoding, model/task/token, high-DPI or production claim.
