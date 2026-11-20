# A02 scope correction

The historical A02 output `PASS_CANDIDATE` covers a synthetic wrapper and a synthetic event identity shape. It is not evidence that the retained producer rows were consumed: A02 assumed a root-level `actuation_id`, while actual `INPUT_EVENTS.jsonl` stores it under `physical_key_measurement.actuation_id` and mirrors it under `physical_key_measurement.adapter_edge.actuation_id`.

Keep A02's raw result and checksums unchanged as historical evidence. Use sibling package `a03/` for the producer-schema-compatible candidate and exact production scorer-pair-validator audit. A03 still uses synthetic schedules and does not execute the V19 backend or scorer tail, controller, OS input, GUI, model, or game. Do not claim live/runtime efficacy.