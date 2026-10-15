# Explicit guarded input recovery

Base main 54790014dd. Design/validation contract: expose the existing session's
release-only recovery on the actual guarded Python/MCP path, without reopening
a connection or replaying a program. Require an open owner, idle serialized input,
exact current binding revision and sticky input-recovery requirement. Invalid or
unneeded requests cause no native call and do not invalidate otherwise valid state.
Python callers must serialize all bridge use; the local active marker is not a
cross-thread/process lock. Standard MCP supplies the serialized worker slot.

An accepted request revokes alias/history scope and advances revision before one
release/readback attempt, including on failure. Old revision requests cannot retry
that attempt. Keep the cleanup ledger and recovery requirement on uncertainty.
Verified empty release clears only that input block. Window review and fresh
grounding remain required for grounded editing, and retired observation/query workers stay retired.
No observation, lease, task success or automatic next action is produced.

One attempt is a finite policy, not an OS time bound. A blocked send/sync/readback
can keep the call pending. Results lookup may report pending; another input,
recovery or close must be busy while the same writer owns the call. Never infer
release from cancellation acknowledgment or pending status. No forced close,
parallel cleanup writer, automatic retry or reconnect.

Fake X validation: public MCP actual bridge/session/backend, blocked cleanup
readback and pending results, rejected concurrent recovery, retained uncertain
ledger, failed recovery, stale revision refusal, explicit verified recovery,
mandatory review/fresh alias, and explicitly chosen new input. Also refuse before
opening a session or without a recovery requirement. Use local normal/-O suites
and relevant distribution checks. Real X/platform recovery and independent task
effect remain unqualified; this work consumes no GUI/container/model allocation.

Python: `bridge.recover_input(current_binding_revision)`. Standard guarded MCP:
`interface_guarded_recover_input(current_binding_revision=...)`, using this
owner's reported `session.binding_revision`. It uses the ordinary busy slot and
returns release-only fields, the consumed/new revision, `review_required`,
`task_success=null` and `replay_allowed=false`. Read the original call through
`interface_results` if its outcome is uncertain; do not replay a lost request.
Failure can follow release effects, so a failed result is not proof of held or
neutral physical state. The retained cleanup ledger drives subsequent explicit
recovery. Existing explicit focus activation is a separate operation; recovery
does not run it or certify its source. No grounded editing resumes automatically.

Python and MCP closure consume the bridge before close I/O, including failed
close. Subsequent Python recovery refuses without revising scope or releasing
input. Closure consumption does not prove successful native close or neutrality.
