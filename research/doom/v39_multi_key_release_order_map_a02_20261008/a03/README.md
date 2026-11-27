# Issue #59 PR-7692 release-order map — A03 real-schema audit

A03 corrects an important scope limitation in the earlier A02 synthetic experiment: retained producer rows do **not** carry a root-level `actuation_id`. The measured identity is nested at `physical_key_measurement.actuation_id`, with a matching value at `physical_key_measurement.adapter_edge.actuation_id`. The original A02 result remains preserved as historical evidence for its synthetic schema; it must not be read as a test of the producer's real event shape.

## Question and test

Can a per-actuation capture map match each release to its admission when identifiers follow the actual producer event schema, while each resulting pair passes PR #7692's exact production scorer validator?

The package pins the exact V19 source, scorer v3 adapter, and the retained producer `INPUT_EVENTS.jsonl` from PR #7692 head `7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e`. It constructs all admission-order × release-order schedules for one, two, and three held unique keys (41 schedules total), clones the actual retained event shape while changing only event identities and timing values, and calls the exact AST-extracted `validate_measured_release_pair` implementation from the pinned scorer adapter.

## Result

`PASS_SCHEMA_AND_VALIDATOR_CANDIDATE`: all 41 candidate pairs passed the production validator with exact final-release identity and an empty held set (1/1, 4/4, 36/36). Six controls passed: missing nested actuation ID, conflicting adapter-edge ID, bool-as-step, duplicate admission, mismatched release, and a production-validator rejection of a changed edge key.

The candidate uses the typed identity `(id, step, owner_id, intent_token, key, physical_key_measurement.actuation_id)`. The raw producer event shape is compatible with this candidate. This validates a synthetic schedule wrapper against actual event shape and an exact production pair validator; it does **not** execute V19's backend class or scorer tail. It does not test a controller, OS input, GUI, model, or game, and does not establish runtime frequency or benefit. Source implementation remains unchanged.

## Reproduce

Python 3.10+:

```powershell
python run_candidate.py
python verify.py
python -m py_compile run_candidate.py verify.py
```

`run_candidate.py` writes `result.json`. `verify.py` independently checks both source hashes, the producer schema, every permutation, recorded boundaries and fail-closed controls. Source/event files and `SHA256SUMS.txt` preserve the exact inputs.