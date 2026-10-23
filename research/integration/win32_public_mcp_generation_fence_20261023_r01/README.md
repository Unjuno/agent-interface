# Public Win32 MCP target-generation fence R01

This one-shot native Windows test carries the generation returned by public
`interface_observe` from one owned fixture process into a later public
`interface_dispatch` configured for a second owned fixture process. The public
static validator must accept the program, while dispatch must refuse the stale
generation before `session.dispatch`. One sentinel text operation targets only
the second owned fixture; the independent event journal must show that no
character was emitted. Each process is closed by the probe, with bounded
termination only for these child processes.

The frozen conditions and standalone auditor are committed before execution.
`probe.py` refuses to run if `raw.json` or `run/` already exists. Any timeout,
cleanup ambiguity, generation alias, or failed check is retained as
FAIL/UNKNOWN and must not be replayed.

The result is scoped to standard public stdio MCP on this Windows host. It does
not establish an atomic check/use fence, input delivery, release under blocked
I/O, supervisor recovery, task effect, MAP01, efficiency, reliability, or WSLc
qualification.

## Frozen trial status

Not yet executed. The source implementation commit is pinned in
`conditions.json`; only an execution of this one-shot packet may update this
section with its immutable outcome.
