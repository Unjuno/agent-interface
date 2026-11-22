# Public recovered-caller fresh lifecycle R03

## Frozen question

Across independent local processes, does the public MCP compiled caller consistently join one fake exact task effect, lost completion receipt, separately verified recovery release/horizon, and exact task-oracle receipt without promoting the source action from UNKNOWN or permitting replay?

## Design

- Run five normal and five `-O` samples, interleaved in the fixed order in `conditions.json`.
- Each sample is a separate interpreter process and creates fresh server, owner, producer, temporary directory, operation/call IDs, recovery receipt, effect row, and task-oracle call.
- Pass only on exit code 0 and unittest `OK`; retain every failure in its original numbered slot and include it in the denominator.
- Do not rerun failed slots, change fixture limits, or replace missing evidence.

This is a local Fake lifecycle repeatability check. It cannot estimate reliability for real GUI input, external task effects, MAP01, or production deployments.
