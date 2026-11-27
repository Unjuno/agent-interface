# R37 — bounded recovery followed by fresh-generation task success

R37 is a one-shot native Windows experiment on the user-authorized local PC.
It uses two sequential, owned fixture processes and two standard supervised
MCP sessions. It does not invoke WSLc or Docker.

Phase 1 reuses the finite blocked-Q-up-callback condition as a new attempt and
must pass the unchanged strict release audit. Only after the first session,
hook and fixture close does phase 2 start. Phase 2 uses a fresh fixture and
target generation, performs one public observation, one validation and one
dispatch, then asks the server-side independent fixture oracle once to verify
the exact click/save/token effect against that action's call, operation and
generation. A pending action may be retrieved only through read-only
`interface_results` for the same call ID.

If phase 1 does not pass its strict gate, phase 2 is not started. Any mismatch,
timeout, duplicate action, oracle binding failure or cleanup uncertainty is
`FAIL_OR_UNKNOWN`; neither phase is retried or replayed. The immutable phase-1
and phase-2 raw records, conditions, source manifests and combined audit remain
in this packet. Run `python run_r37.py --preflight-only`, inspect its retained
input-free PASS receipt, then invoke `python run_r37.py` once within five
minutes; after it returns, invoke `python audit_r37.py` once.

The predecessor packet R37 preserves an input-free preflight failure caused by
an incorrect repository-root calculation. It sent no native input and consumed
no fixture. R37b repairs the path and uses a fresh attempt ID and task token.

This can establish one paired sequence only. It cannot establish broad
reliability, MAP01, matched efficiency, WSLc behavior, real-application
transfer or a hard real-time guarantee beyond the frozen finite windows.
