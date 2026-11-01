# Explicitly owned X11 target retirement in the MCP caller

`create_server(..., _guarded_owned_target_process=handle)` is an experimental,
opt-in Linux/X11 path. The caller must create `handle` with
`OwnedTargetProcess.launch(argv, disposable=True)`, create the application
window, and pass its XID as the sole configured target. The first guarded
session startup binds that XID to the retained child incarnation through XRes
and `/proc` start ticks using a supervised worker. An identity mismatch, worker
failure or timeout prevents guarded requests from starting. The query wait is
bounded after worker creation; process creation and scheduling are outside that
budget.

The optional `_guarded_prestarted_target_identity=True` starts a one-shot
identity worker during server construction. Its request uses the child
session ID after startup; the worker receipt must match that request and the
worker must exit cleanly before its identity observation can bind the target.
If the server is unresponsive, the query times out and refuses the binding;
the worker is retired. A failed query does not authorize input or target
termination. This worker cannot be reused after its one request. Starting it
still has a separate startup cost and is not included in the query deadline.

When the guarded control owner is retired after an unconfirmed or unsafe
cancellation, this owner first terminates and reaps only the bound disposable
target through its pidfd. It then runs the existing independent release and
readback cleanup. The cancellation receipt includes the target binding and
retirement outcome. The canceled task remains UNKNOWN, task success remains
null, and replay remains denied. A failed target retirement is reported as
unknown; it does not turn the original request into success. If a pidfd
signal fails after identity was verified, one immediate further bounded
retirement attempt uses the same handle and retains the first attempt. A
second failure remains UNKNOWN.

This does not adopt arbitrary PIDs or terminate a user-owned application. The
caller retains responsibility for the target handle during normal operation
and shutdown. A successful ordinary close does not terminate the application;
if closing the control owner fails and it is retired, its cleanup may retire
the bound disposable target. If an earlier target retirement was UNKNOWN,
an explicit later close makes one further bounded attempt through the same
owned handle only after the control owner has been confirmed retired. The
receipt retains the previous attempt and the old task remains UNKNOWN. The API is
single-target and Linux/pidfd-specific. It does not yet provide automatic
fresh-process creation or fresh-generation admission.

Target retirement confirms the bound process exited; it does not drain the
X server's input queue or fence input from every other window. X11 input and
focus are shared, so already queued events may be delivered elsewhere after
the server resumes. Use a disposable, isolated display and do not admit a
fresh target solely on the strength of this receipt. The primitive tracks one
process, not a descendant tree or a whole application session.

The handle admits at most one session claim at a time. A verified normal
close, with the control process exited and no execution uncertainty, releases
the claim and clears the old XRes binding; a new owner must bind again. An
UNKNOWN close retains custody, and old session tokens cannot operate after a
release. This is a process-local custody protocol, not an isolation boundary
against code with access to the process or the operating system. During a
cancel transaction, target retirement and its lock wait use a deadline 250 ms
before the transaction deadline, leaving time for the inherited release path.
This reserve does not guarantee release or a hard real-time deadline: earlier
control-owner retirement, operating-system scheduling and X11 I/O can consume
or exceed it. An expired or unavailable target retirement remains UNKNOWN.
The time check immediately before a signal is best effort: scheduling can
intervene before the syscall, and final handle close is not deadline-bounded.
If closing the pidfd reports an error, the receipt records it and the numeric
descriptor is not retried, since it might already have been released and reused;
whether a descriptor leaked remains unknown.
On shutdown with a pending worker, explicit control-owner retirement also
attempts target retirement before the remaining worker drain. A short target
deadline reserves time for escalation from TERM to KILL, but neither deadline
nor process exit guarantees the X server has released held keys. Cleanup keeps
the prestarted supervisor alive until the close attempt ends. If the display
is unavailable beyond that attempt, release may remain UNKNOWN. An explicit
later close does not automatically repeat an unconfirmed input release: the
old client's disconnection cannot prove that another client has not since
pressed the same key. R34 demonstrates that such a retry can release the newer
client's hold. There is currently no fenced public post-resume recovery API;
retain the original UNKNOWN receipt and keep the display isolated.

A real ViZDoom/Xvfb shutdown experiment with a second window focused during
server suspension observed a W press delivered to that window after the bound
target exited and before release. A single repeat-off/on comparison supports
autorepeat as a contributing factor, but does not establish that disabling it
is sufficient or safe. See [shutdown experiment evidence](../../research/integration/vizdoom_mcp_shutdown_r18_r20_20261030/README.md).
An isolated disposable X server must therefore remain under exclusive custody
until cleanup and any required recovery are verified. This code does not
create or enforce that isolation; callers must not interpret target retirement
or a successful key readback as proof that no other client received input.
These unresolved boundaries keep this integration experimental.
