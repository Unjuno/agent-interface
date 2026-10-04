# #59 v39 startup-fault resource ownership construction

**CONFIRMED_STARTUP_OWNERSHIP_GAP_SCOPED.** Exact unmodified controller v39
returns its existing missing-loaded-fixture RuntimeError after acquiring the
session child, without closing that child/reader or calling client.close().
The observed child was a real private subprocess; the client/planner/number
readers and session protocol were explicit inert test boundaries. No actual
v12, game, model or input backend ran.

The normal control and a standard bounded outer-cleanup reference distinguish
this ownership gap. The first normal control had incomplete fake observation
metadata, reached resource shutdown, then raised KeyError in report generation.
Its exact first scripts/raw/error remain under construction01. Only that
ordinary normal control was repaired by adding a fake zero metadata field and
rerun under construction02; the two fault cases were not repeated. These are
four ordinary engineering child runs, not a formal allocation/retry or native
threat-control experiment. Source v39 is never edited.

| Case | At main/wrapper return | Retained outcome |
|---|---|---|
| First normal, incomplete fake metadata | child exit0/client close1 | KeyError capture_to_artifact_ready_ms; preserved construction error |
| Missing ready fixture | child poll None, reader alive, client close0 | existing RuntimeError; no command sent |
| Same fault + standard outer cleanup | child exit0, reader ended, client close1 | same RuntimeError; cleanup before wrapper return |
| Repaired ordinary normal control | child exit0/client close1 | normal return, only FINISH sent |

Child-event monotonic clocks put stdin EOF and child close **after** main-return
in the unwrapped fault, and **before** wrapper-return in the cleanup reference.
The external test supervisor cleaned every owned child/reader/client afterward.
A separate exact-type saved-record reader verifies these joins and rejects six
copied-record corruptions: fake child exit, Boolean close-count alias, wrong
fault, premature cleanup, omitted FINISH and unclosed reference. The first
reader result is retained; a second ordinary wrapped verification reproduces
exact bytes with explicit argv/UTC/exit/log receipt. No candidate is replayed.

| Evidence | Meaning |
|---|---|
| PLAN.json / SOURCE.json | Prospective H/T/D/C/U and exact main/source pins |
| source/ | Exact v39, schema and instruction bytes, inert source snapshots |
| construction01/ | All three first ordinary runs, original helper snapshots and first control error |
| construction02/ | Only the repaired normal control, with explicit fake metadata |
| independent-result*.json / check_saved.py.txt | Separate ordered endpoint/type oracle and six controls |
| PUBLICATION.json | Original/private receipt to public path-redacted derivative hashes |
| SHA256SUMS | All public package bytes; self excluded |

Source is main `816724f93a7239b3ad9b5ebb2e5f79b8a103b2db`; v39 SHA256
`cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`.
The full unmodified module is compiled/executed, with imported heavy boundaries
explicitly substituted. WSL path translation and session argv become local
inert boundaries. Real Python subprocess/stdin/stdout/stderr, reader thread,
atexit registration and the actual main control flow remain. Zero iterations
preclude planner decisions, motor actions, HUD/guard evaluation or authority.
The normal main report's static game/contract fields do not certify execution;
its model/physical/task semantics are unexercised by this construction.

To reproduce in a fresh owned scratch directory, copy this package, rename root
*.py.txt and source/map01_overlap_controller_v39.py.txt to *.py, and run:

```sh
python3 -B run_construction.py --run-id fresh-ordinary-01
python3 -B run_construction.py --run-id fresh-ordinary-02 --case normal --session-child session_child_v2.py
```

These run new ordinary construction children and are not permission to overwrite
retained construction01/02. The default data reader verifies the preserved
construction01/02, not arbitrarily renamed runs: `python3 -B check_saved.py`.
Run it in scratch to preserve original audit bytes. It also reads the first
nominal control failure, so do not omit that record.

## Decision and limit

RETAIN this counterexample as a concrete current-caller setup-recovery blocker.
Do not adopt the fixture's cleanup as a game-input safety mechanism. An absent
fixture might not occur with a correct actual v12; fault injection tests the
explicit existing rejection path, not a natural failure rate. Client is fake;
no actual app-server close latency or model call was measured. Cooperative EOF,
configured waits and these completed runs do not prove bounded noncooperative
process/I/O/journal shutdown, physical release, live threat reaction, useful
game feedback, survival or speed. Actual session EOF/release ownership and
required process/client teardown evidence must precede runtime promotion.

The archive adds no runtime/workflow/import/test-discovery path. All Python
helpers/source are .py.txt. Existing peer #6913 scorer repair and #6915 frozen
owned-Linux-pipe cancellation remain separate and untouched. #59/R134/#57 and
the overall computer-control goal remain open.

Exact historical v39 bytes include a final CRLF blank line. Initial publication
whitespace check reports that source-snapshot line; it is preserved unchanged.
A path-specific archive attribute declares cr-at-eol/-blank-at-eof for only this
inert snapshot. It does not normalize raw/source bytes or relax other paths.
Cross-process counter ordering follows the [Python time contract](https://docs.python.org/3.14/library/time.html#time.perf_counter); these are endpoint-order checks, not latency guarantees.
