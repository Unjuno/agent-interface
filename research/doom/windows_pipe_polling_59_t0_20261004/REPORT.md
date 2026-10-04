# Windows pipe polling repair — Issue #59 construction T0

## H / T / D / C / U

**H.** The retained same-thread scorer poller can consume controller commands
from a redirected Windows anonymous pipe while preserving its scheduled scorer
reads and main-thread game access; source-manifest paths can also remain stable
across Windows and POSIX hosts.

**T.** On Windows 11 / CPython 3.12.10, run the real anonymous-pipe timeout,
delayed-data and EOF tests; the full poller same-thread test; the v13 session
composition tests; and the scorer-adapter tests. The pre-change path failed at
`select.select` with WinError 10093. The Windows implementation now polls
`PeekNamedPipe` at 1 ms intervals, returns readiness at data or broken-pipe EOF,
and leaves reads and game/scorer calls on the caller thread. V13 source keys use
`Path.as_posix()` for cross-platform stability.

**D.** The scoped construction gate passes when the three focused suites pass,
source manifests use stable slash-separated keys, compilation succeeds, and
`git diff --check` is clean. The final run passes poller 13/13, v13 composition
4/4, and scorer adapter 5/5. The broad Doom test discovery run is recorded as
not green: 271 tests, 31 errors and one failure, with missing local VizDoom/WAD
and Xlib prerequisites, omitted workflow files in this sparse worktree, and an
unrelated stale frozen source hash. It is not represented as a green suite.

**C.** Linux `select` remains the existing path. A bounded 1 ms `PeekNamedPipe`
loop trades a small polling cost for command wake latency on Windows pipe input.
Regular-file stdin returns immediately. The implementation does not claim
console-input support.

**U.** This is a Windows-host construction result only. It does not test WSLc,
X11, Doom, a model, live input, task effects, recovery, latency benefit, safety,
or a formal/live MAP01 allocation. The repository-level `test_preregister_...`
hash mismatch remains untouched.

## Reproduction

From the repository root, on Windows:

```powershell
python research/doom/test_main_thread_scorer_polling_v1.py
python research/doom/test_session_map01_v13.py
python research/doom/test_map01_scorer_stdio_adapter_v1.py
python -m py_compile research/doom/main_thread_scorer_polling_v1.py research/doom/session_map01_v13.py
git diff --check
```

Command outputs, Python version, and platform identity are in `results/`; local
user and checkout paths are redacted in the retained broad-suite log.
The relevant API supports the read end of an anonymous pipe and reports bytes
available without consuming them; see Microsoft's [`PeekNamedPipe` reference](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-peeknamedpipe).
