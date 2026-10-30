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
unknown; it does not turn the original request into success.

This does not adopt arbitrary PIDs or terminate a user-owned application. The
caller retains responsibility for the target handle during normal operation
and shutdown. A successful ordinary close does not terminate the application;
if closing the control owner fails and it is retired, its cleanup may retire
the bound disposable target. The API is
single-target and Linux/pidfd-specific. It does not yet provide automatic
fresh-process creation or fresh-generation admission.

Target retirement confirms the bound process exited; it does not drain the
X server's input queue or fence input from every other window. X11 input and
focus are shared, so already queued events may be delivered elsewhere after
the server resumes. Use a disposable, isolated display and do not admit a
fresh target solely on the strength of this receipt. The primitive tracks one
process, not a descendant tree or a whole application session.
