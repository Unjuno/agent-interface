# A01 — Xlib audit-v2 metadata consistency challenge

This is an additive follow-up to the synthetic Xvfb diagnostic merged by PR #7776. It challenges only the report-consistency boundary of its post-run audit-v2 correction; it does not rerun the original one-shot Xvfb candidate.

See H/T/D/C/U and frozen decision rules in FREEZE.json. The treatment mutations replace one top-level value in the retained original RAW.json and recompute the raw JSON digest before submitting it to the unchanged audit-v2 implementation. The independent auditor checks the exact mutation deltas and result matrix from the frozen contract.

Scope: synthetic Xvfb/XTEST evidence provenance only. No current V39 controller, game, model, OS keyboard, physical key, task effect, recovery, safety, or MAP01 outcome was exercised. No GPU/game allocation was requested.

A01's exact-main prelaunch STOP and construction evidence are retained in A01_STOP.json and CONSTRUCTION_A01.json; no formal candidate or auditor ran under that allocation.
