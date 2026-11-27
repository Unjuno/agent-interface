# V39 cancellation across owned Executor child pipes

Base `3e02dec0bf49676ab0ba330b2a3cb97f2925dac4`; tested code
`52fc605599d3c7fd225c66a84564f16556b0f995`. New ordinary test:
`research/doom/test_map01_v39_executor_pipe_recovery.py`. No production changes.

## Actual composition

Parent current V39 cancel helper and exact nested wait AST consume a real
stdout reader queue from owned Python subprocesses. Child workers instantiate
actual Executor v12 (default session selection) or v13 (measurement selection).
A test-only stdin protocol shim calls real submit/cancel/close. Its synthetic
backend signals a simulated held action and then responds to lease cancellation;
there is no X connection, native key state, game or provider.

Each mode runs six selected modules, **67 unique methods, zero failures/errors/
skips**, with eight child pipe cells: health/ammo invalidation on both Executor
versions (four), unknown cleanup on both (two), explicitly dropping invalidation
on both (two). Child optimize flags, interpreter and launcher/parent identities
are retained. Normal and actual optimized runs each create eight distinct owned
children and join their reader/cancel threads. No final cell forced cleanup.

Backend records a synthetic owner release, emits typed and full recovered
sequence12/health96/ammo4, and deliberately blocks before terminal finalization.
At that barrier the parent cancel helper remains pending, no terminal is seen
and planner events contain only local invalidation. Release notification is not
program completion. After explicit fixture resume, actual Executor terminal
crosses the pipe: known empty closure allows planner interruption, unknown
cleanup retains recovery-required custody and aborts without interruption.
The old deliberately eligible answer still fails final admission, while the
latest full recovered observation remains available. Dropping invalidation
makes the same completed old answer reach action validation; it still grants
no input authority. No second program is submitted in any cell.

All complete wire rows, accepted Executor records, final/failure
receipts, barrier/thread states, stderr/exit codes and child source hashes are
retained. 35 unique executed repository Python source joins combine parent
and child loaded-module selections; they are not every dependency or the full
application path. A saved-only reader imports no candidate, checks literal
order/custody/freshness/authority/identity, and rejects six copied contradictions
per mode. The named final launcher/interpreter PID absence snapshot checks32
IDs after all joins; all were absent at that instant. This is not a process-wide
inventory or a future lifecycle guarantee.

## Initial collector correction

An exploratory three-method pipe check passed; only its full stdout/stderr was
retained, before child source metadata was added. The first full normal suite
then passed67 methods and retained all eight rows, but collection stopped on
its false assumption that Windows Popen launcher PID equals interpreter PID.
That complete initial raw/streams/process receipt remain under `initial/`.
The next metadata-only test change records the interpreter's parent PID;
final collection verifies direct identity or the explicit parent relationship,
recording both. These ordinary local checks are not independent live trials.
No original experiment producer was run and no failure evidence overwritten.

## Remaining boundary

This advances helper/AST-only evidence to real pipes and actual Executor worker
threads. The protocol shim and backend remain fixtures: session_map01_v12/v15
main, scorer, actual native backend/owner, pixels, transport failure and full
controller main/model are not run. Fixture release is not physical release or
an OS time bound. Post-failure final-admission calls are no-input counterprobes,
not recovery/resumption permission. Task effects, finite live recovery, useful
feedback, matched token/latency/resource costs and transfer remain unqualified.
No GUI/game/native input/model/provider/WSL/container/allocation ran.
Keep #59/#57/#17 open. Next connect the actual session/backend ownership and
process-failure boundary before claiming live control or physical release.
