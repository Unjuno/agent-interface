# Issue #3587 — explicit public-MCP post-action observation

This experiment checks one narrow integration step in the public portable MCP
path: after one action response, a caller can make a new read-only observation
and obtain an image of the independently saved fixture state. It is not a host
registration or model-visibility experiment.

## Status

Formal allocation has not yet run. `PREREGISTRATION.md` is committed before the
three formal allocations. One excluded construction allocation on the exact
frozen main archive is retained separately beneath
`evidence/construction-excluded/`. It is not a formal row and is excluded from
the result denominator. Preserve any later STOP, FAIL or audit disagreement;
do not retry or replace a formal allocation.

## Boundaries

- The fixture-side JSON file is the independent saved-effect oracle.
- X11 PNGs and image blocks establish artifact identity. A pixel difference is
  not itself semantic task success.
- `interface_observe` is read-only and does not refresh input authority or
  score the application effect.
- This does not observe host presentation acknowledgement, model-visible
  receipt, model interpretation, useful-feedback latency, model usage/cost,
  broad application reliability, or performance improvement.
- Issue #3370 remains open regardless of this scoped result.

## Reproduction

Use the pinned OrbStack image and exact portable archive in `freeze/`. The
runner is `container_smoke.py`; the raw-only auditor is `audit.py`. Each formal
allocation uses a fresh evidence directory mounted writable while the runtime
source and archive are mounted read-only. Container networking is disabled and
the container root filesystem is read-only.
