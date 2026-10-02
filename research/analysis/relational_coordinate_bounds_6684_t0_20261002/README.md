# Issue #6684 T0 — relational coordinate-bounds method experiment

This additive package tests whether retaining a shared viewport translation in action-minus-target bounds can reduce conservative refusals compared with independent coordinate boxes. It uses a deterministic finite integer grid, immutable intended-target IDs, an adjacent forbidden hitbox, bounded scale/shift/calibration variables, and a separately implemented exact-state auditor.

It does not modify or reinterpret #5577 or #18/#4150 outcomes. No runtime code, model, GUI, user data, network, or OS input is involved. No coordinate abstraction grants target selection or action authority; uncertainty returns `UNKNOWN_REOBSERVE`.

The frozen H/T/D/C/U, finite-state semantics, count limit, and decision gates are in [`PREREGISTRATION.md`](PREREGISTRATION.md). Construction tests:

```bash
python3 -B -m unittest discover -s research/analysis/relational_coordinate_bounds_6684_t0_20261002 -p 'test_*.py' -v
```

The formal candidate and independent exact enumerator, environment, raw output, audit and run record are retained in `results/formal-01/` after the one-shot allocation.
