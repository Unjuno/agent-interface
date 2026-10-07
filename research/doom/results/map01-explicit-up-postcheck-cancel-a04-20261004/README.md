# Explicit-up cancellation boundary A04

A03 captured the forced cancellation/KeyRelease ordering, then stopped in its post-up fake `input_state` observation because `FakeRoot.query_pointer()` lacked `root_x`/`root_y`. A03 and both audits remain preserved. A04 changes only the fake pointer fields and run ID; the tested owner, wrapper, cancellation schedule, and decision gate are unchanged.

This is a separate construction invocation, frozen under a new ID. OrbStack preflight remains unavailable; the candidate uses host Python and fake Xlib only, with no container portability or live system claim.

## Reproduction

```sh
python3 candidate.py
python3 audit.py
```

Run the candidate once. See `PLAN.md`, `FREEZE.json`, `ENVIRONMENT.json`, and exact `source_snapshot/`.
