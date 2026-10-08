# A6 — X11 temporal capture cadence 15 Hz

Issue #1078. BASE `2424b69785a526b8ea4e2e49a5052678f16b1d13`.

H: with A4/A5 mechanics fixed, 15 Hz bisects the retained 10 Hz PASS / 20 Hz REJECT cadence contrast.

T: private Xvfb/Tk 320x240; baseline no capture vs raw full-frame XGetImage at 15 Hz with 500 ms bounded raw ring; 300 ms warmup; 1500 ms measured; six fresh counterbalanced pairs; one formal invocation; no reruns/replacements/tuning.

D: PASS_X11_TEMPORAL_CAPTURE_15HZ_SCOPED iff capture>=18/arm, exceptions0, drops<=1, capture p95<10 ms, CPU<0.20, ring<=10 frames, paired median fixture-count ratio in [0.97,1.03], paired median p95-gap increase<=2 ms, and candidate max-gap excess<=10 ms. HOLD only if >=2 baseline max gaps>100 ms. Otherwise REJECT_CAPTURE_COST_AT_15HZ.

C: A4 may reflect non-monotone host scheduling noise rather than a cadence threshold.

U: Xvfb/Tk/python-xlib, 320x240 raw only; no real compositor, encoding, high-DPI, model/task/token or production claim.
