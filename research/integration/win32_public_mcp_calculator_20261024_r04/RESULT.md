# R04 result — static validation stopped before input

R04 obtained a fresh public MCP observation of the authorized Calculator target (Standard mode, display 1,042; target generation matched). Its frozen program included one clear click followed by the computation. Validation rejected it with `INVALID_PROGRAM`, detail `invalid program_id`, before runtime admission. The generated identifier was 73 characters; the contract allows 1–64. Dispatch was never called, input was not sent, and the MCP session closed with zero calls and no unresolved IDs.

This is a harness setup failure, not an application or runtime action result. The prior R03 bug is corrected in the runner, but R04 exposed an overlong identifier. The attempt is preserved; any follow-up requires a distinct ID and a short valid program identifier.
