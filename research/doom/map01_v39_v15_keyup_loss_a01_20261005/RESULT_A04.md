# V39/V15 dropped KeyRelease probe — A04

A04 is a preserved constructor STOP against current-main source `402c7d1b5147b2a905098f082233db60a47d68db`. The candidate failed before either paired case started (`AttributeError: 'NoneType' object has no attribute 'close'`) because the test-only base controller did not satisfy the production V2/V15 constructor-owner contract. The frozen one-run rule was honored; no A04 audit ran and no per-program cleanup behavior was measured. See `FREEZE_A04.json`, `results/candidate-a04/STOP.json`, and `RUN_COMMANDS.md`.

A03 remains a bounded fake-X batch failure: an injected lost KeyRelease left keycode 38 down while the release-batch row was owner-transition-verified. A03 called owner close after the direct backend batch; it did not execute V13's production per-program cleanup. A later corrected harness is preserved as `candidate_a05_unrun.py` / `audit_a05_unrun.py`; it was never executed and is not evidence. The live #59 gate remains unresolved.
