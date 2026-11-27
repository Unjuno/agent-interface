# Issue #57 prospective deferred/unknown usage custody — R04

## Scope
Windows CPython 3.13.14; Pillow 12.2.0. Extends the synthetic `ModelFailure` path through the v3 caller, durable Calc allocation and registered `ProspectiveRun` task custodian. Two cases: `FAILED_UPSTREAM` with usage UNKNOWN, and `DEFERRED_UPSTREAM` with known synthetic usage. One task row per fresh local run; no provider, GUI, native input, Docker, WSL, or dispatch.

## Pass rule
Both cases must preserve the caller's typed outcome and attempt usage in the durable custodian; the custody audit must pass; projection and incomplete run must remain HOLD. The full App Server usage/custody test module must pass normally and under `-O`.

## Results
The final fixed module passes 4/4 normally and 4/4 under `-O` (exit 0). Both unknown-usage failure and deferred-with-known-usage reach registered custody and are audited. The frozen v1 task projection remains HOLD (`failed_attempt_not_representable_in_v1`) and finalization remains HOLD because this one-row run is incomplete.

## Failure retained
The first run failed in both modes because the synthetic `anchor_model` callback was declared with five positional parameters while the public caller contract supplies one payload. This was a fixture error, not an observed product failure. The callback was corrected to the documented one-argument shape; the first raw stderr and exit status remain here and are excluded from pass counts.

## Limits
The peer/model are synthetic. This does not test real provider usage, successful answer/effect, live GUI, all 18 assignments, or a matched efficiency comparison. The deferred case uses a caller-level typed synthetic `ModelFailure`, not an App Server provider response. Keep #57 open.
