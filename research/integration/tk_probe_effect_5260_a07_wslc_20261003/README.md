# #5260 A07 focus-probe-effect FIRST STOP
Executed eight fresh privateTk apps in WSLc; independent first audit STOP is
retained verbatim. This is **not** a method/H PASS or a Docker/WSLc resource claim.
See [REPORT.md](REPORT.md), original [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json)
and [RUN.json](RUN.json). First source/raw/frames/app streams/host streams are exact.

Read-only revalidation (never invokes candidate, app, container or input):

```powershell
python -B -m unittest discover -s research/integration/tk_probe_effect_5260_a07_wslc_20261003 -p 'test_*.py' -v
python -B research/integration/tk_probe_effect_5260_a07_wslc_20261003/verify_packet.py
```

Expected packet status is PASS_RETAINED_FIRST_STOP_ONLY; scientific status stays
STOP_AUDIT/UNQUALIFIED. Original once-only host_capture commands remain historical,
not instructions to replay. Prepare a new source/environment/allocation for any
successor. No user display/model/GPU/global configuration or runtime code changed.
Refs #5260/#5296/#5085; predecessors PR#7112/#7122/#7130.

