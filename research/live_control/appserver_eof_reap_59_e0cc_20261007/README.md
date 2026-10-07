# Reap an exited app-server leader before signaling its group

On macOS 27.0.1 arm64 / bundled Python 3.12.14, an inert app-server child
could exit and wake its notification waiter, yet `close()` raised
`PermissionError` at `os.killpg(SIGTERM)` before reaping that child. A separate
unpatched-client diagnostic reproduced the error after reader EOF; explicitly
reaping the child first made close succeed. This was discovered while checking
the real transport composition of [#8280](https://github.com/Unjuno/agent-interface/pull/8280).
It is a client cleanup defect, not evidence of a leaked child or failed wakeup.

The patch polls the owned leader before signaling and still signals the group
to retire surviving descendants. If the leader exits between poll and signal,
one recheck/reap and signal attempt handles that race. A live leader's denial
and a persistent group denial remain errors. Custom process factories retain
their existing cleanup path. No controller, planner, timeout, or permission
policy is changed.

Base main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`. The client and existing
process-tree test module are the only executable files changed. That module is
already registered in `runtime/integration_checks/native.py`. The archive here
is passive evidence and is not imported or discovered as tests.

## Validation

- Before repair, five added tests produced two failures, two errors and one
  pass; the actual EOF-child error and first traceback are retained.
- After repair, all eight process-tree methods passed, including the existing
  three real POSIX descendant cases with ignored SIGTERM/inherited or detached
  pipes. Deterministic controls retain live and persistent permission denials.
- Seven focused client modules passed 29 methods normally and 29 under `-O`.
  Compile, diff whitespace and 22 workspace-index methods also passed.
- Existing bugbot reviewed the change and independently audited the original
  controller raw records, passing 18 checks. This is helper verification, not
  the required whole-PR nonauthor quorum.

The original eight controller cells use the exact #8280 predecessor
`6ec463eb907377ba41191127f4ea569d9ecfe142` and follow-up
`029064c797768183f63c79bbedbe3aca18f85dbb`. They exercise actual V39 main,
ThreadPoolExecutor, planner adapter, default Popen client and a local inert
JSONL peer, with a synthetic application session, observations and cleanup spy.

| Interrupt response | Predecessor | #8280 follow-up |
|---|---|---|
| Error, no completion | External close required | Transport abort wakes waiter |
| Acknowledgment and completed answer | Answer ineligible | Answer ineligible |
| EOF | Waiter wakes | Waiter wakes; close reports the retained EPERM |
| Acknowledgment, no completion | External close required | External close required |

Two additional ordinary regression cells overlay only the repaired client on
the 67-file #8280 export. EOF and interrupt-error cases both preserve the original
cover failure, make no further submission, reach cleanup, and retire the future,
reader, actual child and process group without external rescue or abort error.
The remotely advanced #8280 branch and all original evidence remain unchanged.

## Evidence and reproduction

`MANIFEST.json` hashes all 285 members of `evidence.tar.xz`, including the
original 8-cell protocol/freeze, exact source exports, portable harness and peer,
wire logs, traces, execution records, independent auditor, unreaped/reaped
diagnostic, failing regression, repair diff, test logs and two repaired cells.
Archive readback checked every member. `RESULT.json` records the scoped result
and source/test hashes. Only absolute workspace/runtime prefixes in 24 text
members were projected for publication; the manifest retains original and
published hashes. Original local files are preserved.

From repository root, with `research/live_control` on `PYTHONPATH`, run:

```sh
python -m unittest -v test_appserver_process_tree_cleanup_20261004
```

The other focused modules are `test_app_server_eof_stop`,
`test_app_server_reply_id_5156`, `test_app_server_utf8`,
`test_appserver_utf8_2d0b`, `test_appserver_reader_retirement_01a0ff2d`, and
`test_appserver_journal_close_01a0ff2d`. Exact execution commands are retained.
In an extracted evidence directory, `python audit-bugbot.py` re-audits the eight
original cells and rewrites only its derived audit outputs; inspect its JSON
`overall_pass` field. No producer execution is needed for that audit.

## Limits and disposition

These are ordinary repair tests, not a consumed live-game allocation. No Codex
model, external app-server, GUI, game, native input, VM or shared model service
was used. Process lifecycle checks used real host OS children. The synthetic
cleanup spy proves handler entry, not production cleanup or physical release.
One schedule per controller condition and fixed arm order do not establish a
latency distribution or OS shutdown worst-case bound. The one-second external
watchdog censored incomplete controls; no full 90-second wait was measured.
An acknowledged interrupt without completion remains outside this repair.
Persistent close failures remain reportable.

Draft repair for nonauthor review and fresh current-main integration. No main
update or live task-effect/recovery claim follows from these results. Peer
response-ownership and lifecycle proposals, including #8186, remain separate.
