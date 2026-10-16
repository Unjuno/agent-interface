# Construction history (not the T1 scientific allocation)

2026-10-03: exact-pixel decoder and equal-eight-capture schedule were tested
before implementation. The initial skeleton returned `None` / `[]`.
The first five-test command exited 1: three failures (red cue, green cue,
equal-budget schedule); dark/malformed-pixel controls passed vacuously.
An additional malformed-cycle test was added and the six-test red output
is retained in `construction/policy-red.json`. This is ordinary construction,
not physical X11 evidence. No transient/phase comparison was run.

Command: `python3 -B -m unittest discover -s
research/live_control/phase_diversified_capture_6067_t1_20261003_3cbf
-p 'test_policy.py' -v` from repository root.
