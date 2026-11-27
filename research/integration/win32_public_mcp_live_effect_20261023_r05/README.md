# Public stdio MCP live Win32 effect R05

Fresh one-shot experiment pinned to source commit `28db8816564e88dd54d15de716d939a8e51bdb9f`, which adds a scoped `GetAsyncKeyState` availability witness using the active input desktop, foreground target, desktop access and process integrity. It uses the actual stdio MCP server and public observe, validate, and at most one dispatch call against a new owned fixture.

PASS requires returned observation and static validation, exact independently read fixture effect/event counts, one save, and a verified release receipt. Any timeout or UNKNOWN is preserved and never replayed. The R03 failure remains immutable.

Nonclaims: release under a blocked API, hard release-time bound, supervisor recovery, target-generation admission fencing, model/token efficiency, MAP01, and broad reliability.
## R05 frozen outcome and extraction defect

The frozen R05 auditor reports 11/12 checks and `FAIL`; the raw top-level status remains `FAIL_OR_UNKNOWN`, and it is never rewritten or replayed. Reviewing the retained public dispatch report exposed a probe bug: the reporter searched for `retained_report.execution.releases`, while the public report schema stores this under `retained_report.result.execution.releases`. As a result the frozen `release_receipt` field was empty and the auditor could not score release, although the retained public response itself records `result.status=completed`, one release receipt with `verified=true`, empty down/unknown key/button lists, and stable active-desktop query witnesses. The independent fixture effect and exact event oracle also match.

This forensic observation does not change R05's frozen classification to PASS. R06 is a separate fresh fixture, attempt ID, task string, and pre-run auditor with the corrected report path. It will be the only qualification attempt with that correction.
