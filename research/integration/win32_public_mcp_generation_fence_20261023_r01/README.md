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

The one-shot trial passed all 14 frozen audit checks on 2026-10-23. Public
`interface_observe` returned fixture A's generation
`ef18c0b020d17e6cd1539c360151415211fba6f2e6d4e0b9200cec2fc9a8183f`; a distinct
owned process B had generation
`28c594d18663aed3b7e82f018bc6a8df42474e5e4a2a0a275f03db13143d6d09`. Public
static validation accepted the program carrying A's generation, and the one
public dispatch returned `TARGET_GENERATION_CHANGED` with
`input_dispatched=false` and `operation_invoked=false`. Fixture B recorded only
its `ready` event; its effect file was absent. Both windows closed and both
owned processes exited 0. The frozen audit is `audit.json`; the full public
responses, fixture event files, call reports, and capture artifact are retained
under `run/`. `raw.json` SHA-256 is
`6ff82e90119d280fd1e0071bee7f26514b8ab0a5012e2265cfc49bc37aa993d6`.

This qualifies stale target-generation refusal through the standard public
stdio-MCP caller for this owned-process replacement case. It does not close the
post-check/use race or qualify accepted input, release, recovery, task effect,
MAP01, efficiency, broad reliability, or WSLc.
