# Preregistration addendum — fresh stale-source allocation

The first allocation is frozen as `STOP_OBSERVE_RESPONSE_SHAPE` in
`PREFLIGHT_STOP.md`; it is not retried or counted as a stale-input trial. Its
raw files remain unchanged.

For the next fresh allocation only, the client now resolves stage status through
the exact compact receipt path `receipt.native_result.status`, keeps each raw
MCP result before interpretation, and requires observation sequence 2 before
the stale stage-2 call. All other H/T/D/C/U gates in `PREREGISTRATION.md` remain
unchanged. The same fixed seed and main/image/runtime are retained; this is a
new owner/process/allocation and a new evidence directory
`evidence/stale_source_v2/`. No attempt is made to repair or continue the prior
owner. The new client hash is frozen in `SOURCE_FREEZE_V2.json` before launch.
