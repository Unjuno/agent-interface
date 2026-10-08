# Discoverable native decision fields

The MCP native_submit decision previously appeared as an unrestricted object.
A model seeing tools/list could not learn the source_sequence, point, expected
title, tail or finish flags from the schema. The adapter now exposes typed fields
and operation examples. Actions require point and expected_title; finish=true
can terminate without another action. Strict flags reject strings/integers and
finish+finish_after conflicts before immutable request publication.

Defaults are documentation only until explicitly supplied: model_dump excludes
unset fields. Existing extension fields remain available and unchanged. This
validates the envelope, not every tail opcode, target semantics or authority.
Runtime source, target, admission, release and duplicate checks still apply.
Conditional point/title requirements appear in the model description and are
enforced by validation; JSON Schema's required list contains source_sequence.

39 tests pass. The actual stdio tools/list result contains the decision fields;
six malformed requests are rejected with no request file. Correct finish/action
and extension payloads preserve encoded bytes. `check.py` independently checks
six exact copied live requests from native-combined-batch-01 and
native-direct-stdin-01 against the new parser. This is compatibility evidence,
not new model or GUI execution. The script imports the parser being checked and
is not an independent implementation of its validation rules.

No new sensor, controller, automatic default action or host registration.
Model usability, success rate, schema-token overhead and latency remain
unmeasured. Existing malformed-input behavior intentionally changes from late
harness failure to pre-publication rejection at this MCP adapter boundary.
