# Issue #3610 — first proxy effect-binding unit

Parent idea: [#3584](https://github.com/Unjuno/agent-interface/issues/3584). Formal allocation: `issue3610-proxy-effect-unit-formal-01`.

The immutable hypothesis, test matrix, decision gates, scope, and unknowns are recorded in `PREREGISTRATION.md` and Issue #3610. `PRECHECKS.md` records excluded construction work and its initial teardown failure. `FREEZE.json` and `SOURCE_MANIFEST.json` bind the source and container before the formal invocation. The formal runner writes lossless row records and raw frame bytes to its fresh output directory; `audit.py` independently replays the conditions without importing the runner.

This is the first safety/effect-binding unit for the task-specific virtual GUI idea. No model or human agent is involved, so there is no usability or arm-superiority inference.
