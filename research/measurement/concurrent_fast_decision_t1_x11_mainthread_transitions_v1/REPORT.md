# #1429 first construction outcome

Decision: **STOP_MAINTHREAD_TRANSITION_INSUFFICIENT**. Scientific disposition: **NONE**.

Exactly one ACTIVATE18 matched pair / two fresh child processes ran; formal0/reruns0/replacements0/tuning0.

The allowed factor succeeded:
- actual CLEAR/WATCH transitions are retained in both rows;
- candidate first CLEAR transition occurred at +18.506 ms and first useful effect at +21.192 ms, latency **2.686 ms**;
- candidate produced two useful effects while CLEAR;
- child exits0/0, terminal F8 UP2/2, cleanup2/2, residual Xvfb0.

A new live TOCTOU race was exposed at the CLEAR->WATCH boundary:
- candidate 30 ms sample ended at +30.070 ms and still observed CLEAR;
- third F8 send ran +30.073..30.137 ms;
- actual WATCH transition occurred at +30.323 ms;
- application press/release/effect were processed after that transition; effect at +30.538 ms was classified harm;
- final score: progress200 pixels, harm100 pixels.

Therefore main-thread transition delivery fixes the missing-transition harness defect, but the current sample->send path does not satisfy the inherited zero-WATCH-effect safety gate under a state change between admission and application effect.

Raw result SHA-256: `6ff23ecfd2e557c91bd1561d67109cdd38c82e170683221e12b8d6e300cdf7f1`.
Audit SHA-256: `6c39786faa49e3218e2a611cabbddd746e2042e698731c82b16a79f907f1f817`.

No rerun is allowed. The next research question is no longer a harness-lifecycle defect: it is the actuation-currentness race between fresh observation/admission and effect realization.
