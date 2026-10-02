# Observation-fiber updateability T0

Allocation: `view-updateability-5368-t0-hostcpu-20261003-a01`  
Successor Issue: [#6774](https://github.com/Unjuno/agent-interface/issues/6774)  
Parent research: [#5368](https://github.com/Unjuno/agent-interface/issues/5368)  
Frozen base: `main@7446e22459ad79f57828b5699b95ef3c0b504917`

This finite synthetic test asks whether an action is invariant over every full state compatible with a partial observation. It compares a freshness-plus-visible-label baseline against a fiber-complete gate. The fixture includes ambiguous duplicate labels, retained-discriminator and irrelevant-hidden-field controls, modal/selection/layout-generation distinctions, an impossible request, a collateral-effect mutant, and an explicit out-of-model case.

## Frozen execution protocol

The candidate is `gate.py`; its single invocation writes `candidate.jsonl` and `baseline.jsonl` with exclusive-create semantics. After that, invoke `audit.py` exactly once; it independently reconstructs observation fibers and effect admissibility from `fixture.json`, does not import the candidate, and writes `audit.json` with exclusive-create semantics. Existing output files make accidental retries fail closed. Do not delete or overwrite raw output to retry.

Construction-only checks before source freeze: Python syntax compilation and fixture JSON/schema inspection. Formal candidate and auditor invocations occur only after `FREEZE.json` is committed. Host Windows CPU only; no WSLc/container/GPU/network/model/GUI/input. Synthetic success is scoped to this declared finite state universe and is not live safety evidence.

## Output interpretation

- `ADMIT`: every enumerated compatible world realizes the requested effect on the requested target without listed forbidden collateral.
- `NEEDS_DISAMBIGUATING_OBSERVATION`: both admissible and inadmissible worlds remain; `hint` is the first field in the predeclared ladder that separates the two classes.
- `UNTRANSLATABLE`: no compatible world realizes the requested effect, or no declared field separates a mixed fiber.
- `UNKNOWN_MODEL`: model coverage is explicitly absent; no effect is authorized.

The candidate emits decisions only, never authority or effects. The raw-only audit is the sole formal check of candidate outputs against the frozen fixture and its manually declared expected labels.

