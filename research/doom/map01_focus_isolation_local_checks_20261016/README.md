# Selected MAP01 focus-read isolation: retained local checks

V39/V15's explicit process-identity selection previously read identity through a
separate client but still queried focus on V12's input thread. `invalid_focus`
ran before held-input cancellation/expiry cleanup. A blocked focus call therefore
kept the fake key held. `blocked-focus-red.log` preserves the first regression
failure on base `41946fdf1c661d5209aa834494e1137179e33ad3` plus the new test:
no interruption arrived during its 200 ms cancellation wait, before the harness
resumed focus in `finally`. This is a finite constructed failure, not a live run.

Selected lease-bound exact focus queries now share the independently owned
read-only target worker with process queries. The existing subtree-focus query
and default direct-focus owner remain available unchanged. Original deadline,
cancel and stop fence the wait and late result; failure/malformed evidence retires
the reader. Release never reads focus. A failed query records
`target_query_invalidated`, whereas a returned different focus records
`focus_changed`. Receipts retain the pending/retired reader and query-failure flag.

Owner tests check held cancellation and original expiry release before focus
resumes, failure/malformed/change distinction, and pre-press cancellation with no
late input. Existing final-focus cancellation/source/deadline mutation tests now
cross that worker too. The actual selected backend/Executor/V4/V12 test checks a
non-completed terminal with verified fake release while the focus read is still
blocked. Runtime reader coverage confirms exact-focus I/O runs on its worker
thread and retains the separate existing subtree semantics.

`normal/` and `optimized/` preserve all 33 isolated module logs and summaries from
clean source `0365189f41063548f1bfb16880bd1de7090b0c41`. Both report 249 methods,
zero failures, one deliberate optional real-Codex handshake skip (248 executed).
Commands used `../check_map01_control_regressions.py --output-dir <fresh path>`,
adding `--optimized` for the second run. Host: Windows, Python 3.13.14,
python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0, openpyxl 3.1.5. First RED and
intermediate normal/-O runs remain in the local consolidation evidence directory.
`MANIFEST.json` hashes every retained file except itself.

No live X/GUI/game/provider/model/container/allocation was launched. The test
patches clients with Fake X objects. This is a named focus-read isolation result,
not a native/physical release time bound. Input send/sync/readback, pointer
geometry/hit testing and idle observation can still block. A retired read-only
daemon can remain pending until its I/O returns. Process incarnation still does
not establish window incarnation or atomic server acceptance. Independent task
effect, finite task recovery and matched efficiency remain unqualified. Historical
generation-gap and previous regression packets are unchanged.
