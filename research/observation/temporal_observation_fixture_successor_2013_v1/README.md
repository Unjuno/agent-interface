# Temporal observation fixture successor #2013

This additive path is a preregistration and source-freeze boundary for Issue #2013. It is not a runtime implementation and contains no live GUI, model, network, or input action.

## Scope

Compare current-only observation with a bounded temporal-ring query over one controlled GUI-like state fixture. The fixture will include a known transition, one event anchor, dropped-capture intervals, one ROI, one full-surface query, and explicit current/historical roles.

## Decision boundary

A scoped PASS requires exact preservation of source IDs, timestamps, scope identity, current/historical roles, ROI transforms, and unavailable/drop intervals. Missing observations must never be represented as unchanged. Any historical evidence becoming current authority is STOP.

## Execution boundary

The next commit may add only deterministic standard-library fixture code, raw output, an independent audit, and environment metadata. One isolated container run is permitted. No GUI/X11, model, network, task input, or runtime promotion claim is authorized by this path.

Status: PREREGISTERED_NOT_RUN
