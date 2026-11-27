# V39 post-batch keymap fault recovery A06

This successor repairs the consumed A05 harness defects. It drops at most one
SPACE key-up, allows the owner's cleanup retry through, and fsyncs each case
to `results/A06/RAW.jsonl` before starting the next. A query failure is kept as
an explicit HOLD row. The probe uses the production release-batch backend and
V4/V3/current V12 owner with an inert fake X display and scripted lower typed
backend.

Run `python3 build_freeze.py` once, then `python3 run_candidate.py` once, then
`python3 audit.py`. The runner refuses a changed main/source/artifact freeze or
existing output. Do not rerun the candidate; preserve a STOP result and create
a separately frozen successor if the harness fails.

The result can qualify only fake-Xlib cleanup and evidence custody. It cannot
establish physical key state, application consumption, live latency, useful
feedback, bounded recovery, threat response, or MAP01 behavior. The private
live-game lane remains outside this probe.
