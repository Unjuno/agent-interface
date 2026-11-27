# R26 result — supported maximum still returns pending

The frozen trial remains `FAIL_OR_UNKNOWN` (8/12 strict checks). The 10,000 ms
wait was accepted, but the public dispatch returned `pending` after
10,010.560 ms. Public `interface_close` returned `busy` with
`release_confirmed=false`; the later session-close record says `closed` and
still leaves release unconfirmed. No replay or second dispatch occurred.

The exact independent fixture effect committed 10,835.722 ms after dispatch
start. The persisted runtime report later records completed execution and a
verified all-up release at 10,852.859 ms, followed by producer exit and neutral
readback at 10,915.859 ms. The independent journal contains exactly one click,
all 32 expected characters, and one save. The owned fixture exited with code
0, and the previous foreground window was restored. An additive 10/10 audit
confirms these later records while retaining the strict `FAIL_OR_UNKNOWN`
outcome.

The distinction from R24 is measurement scale: R26 used the supported 10 s
maximum, and the operation still exceeded it. Both runs show why the caller
must follow the pending receipt's explicit instruction to retrieve the same
call ID. R24 and R26 probes closed too early; the next fresh attempt will poll
read-only `interface_results(call_id)` for a bounded 15 s before closing. It
will use a new fixture, generation, session, program, lease, and sentinel. This
does not retry either prior action. Runtime `task_success` remains null; these
single-fixture outcomes do not establish a broad latency bound.
