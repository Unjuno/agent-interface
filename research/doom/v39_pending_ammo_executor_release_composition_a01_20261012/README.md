# Executor release composition A01

This package joins the exact current-main V39 paired ammo monitor and controller cancellation helper to the exact current-main PersistentPlannerAdapter, Executor v13, and InputOwner V4→V3→V12. It uses an in-memory fake XTest server; it sends no host input.

- Hypothesis and decision rule: `HYPOTHESIS.md`
- Frozen main/source/test identities: `FREEZE.json`
- Exact candidate output/exit: `results/`
- Independent raw/source audit: `audit_composition.py`
- SHA-256 inventory: `SHA256SUMS`

Reproduction: bind this directory into the pinned WSLc Python environment and run `python3 -m unittest -v test_composition` with network disabled, one CPU, and 512 MiB requested memory. The environment warned that swap cgroups are unavailable; do not infer full memory-limit enforcement.

Disposition is limited to deterministic source composition. Fake XTest keymap receipts are not X-server, physical-input, target-app, game, or threat evidence. This is not a live allocation or MAP01 result.
