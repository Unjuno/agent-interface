# Issue #4990 — optimized-Python hardening for typed negative outcomes

Additive successor to #4967. It checks that finite contract decision gates and the 384-row output remain valid under ordinary Python, `python -O`, and `PYTHONOPTIMIZE=1`; the #4967 source and digest are immutable comparison inputs. No GPU/model/training/GUI/runtime effect is in scope.

Issue #4990 is open and this dedicated branch is based on main `7d1208cf323408897983ef2b5c75fd34f54d6815`. Allocation: `typed-negative-outcomes-opt-check-39-20260928-01`. Formal local-container invocation count: 0; no result exists yet. All source/input and a fresh exact-image local Docker invocation need to be frozen before the test block; preserve a typed STOP/FAIL without retry.
