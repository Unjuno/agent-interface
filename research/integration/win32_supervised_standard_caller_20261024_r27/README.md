# Win32 supervised standard-caller R27 — exact-call result retrieval

R24 and R26 each returned `pending` at the public dispatch wait and completed
later in the persisted report. Both probes then called `interface_close`
immediately, so neither tested the documented read-only result retrieval.
R25 established that waits above 10,000 ms are rejected before input. R27 uses
the supported 10 s wait and, if it returns pending, polls
`interface_results(call_id)` for that exact call ID every 200 ms for at most
15 s before closing.

R27 uses a fresh fixture, generation, supervised MCP session, program, lease,
and sentinel. The input-free preflight checks the immutable R26 action/effect/
release receipts and the R25 no-input refusal. The public result lookup must
return the terminal action record with its verified release receipt; the
independent fixture file and event journal provide the separate effect oracle.

PASS requires the pending dispatch, terminal exact-call retrieval within the
15 s bound, completed action, verified all-up release, exact independent
effect, successful public session close, clean fixture exit, and foreground
restoration. Retrieval cannot replay or dispatch input. Any retrieval timeout
remains UNKNOWN, and no redispatch is permitted. Runtime `task_success` remains
null.
