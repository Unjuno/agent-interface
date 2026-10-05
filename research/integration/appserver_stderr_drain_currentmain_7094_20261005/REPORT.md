# App-server stderr drain — current-main successor validation

Status: `SCOPED_TARGET_PASS / NATIVE_FULL_MACOS_BASELINE_FAIL / CONTAINER_STOP / REVIEW_HOLD`.

The detailed first validation below used base `1fa854d`. Before publication,
the successor was synchronized to live main `cd3a410a930e5f1e29a22cee36d9a149fbc106c7`;
post-sync evidence is recorded at the end of this report.

This is a current-main integration check of the already executed #7094 repair,
not a new live app-server, model, GUI, or task-effect experiment. The original
branch and its first outcomes are unchanged.

## H/T/D/C/U

- **H — hypothesis:** when a child writes enough diagnostic bytes to fill its
  stderr pipe, an undrained pipe can prevent the JSONL response reader from
  making progress. Retiring the journal before stderr reaches EOF can lose
  evidence. A bounded independent stderr reader should preserve response
  progress, exact bounded bytes, and close-time retirement boundaries.
- **T — treatment:** integrate the existing #7094 source commit
  `e7f71d63405e1fdd20580fe8f3a893081ecbc94b` and its #7094 current-main merge
  `506a0a47fc643af7add7a3a9a4d9b3b47dd0d29a` onto current main
  `1fa854d537bfd711b5dfd99f8c04ab6c35bad286`. Conflict resolution retained
  main's process-tree cleanup and UTF-8 test registration, then added the
  stderr-reader join and stderr regression-suite registration. The initial
  successor checkpoint was `rescue/7094-appserver-stderr-currentmain-20261005`, head
  `91cffcc13286b3d2956b7afe4d272254a6f707fc`; its first commit
  `bdf8383b744c929625b8ac1ccb17709141c60211` adds the regression test before
  the source merge.
- **D — data:** on the unmodified current-main code plus the new test, the five
  stderr-drain tests failed as expected (5 failures, no test errors): large
  stderr blocked the response; bounded-tail response also timed out; the
  stderr snapshot/reader behaviors were absent; and close retired the journal
  before stderr EOF. After integration, the six related modules passed 24/24
  on CPython 3.12.13 both normally and under `python -O`.
- **C — controls:** the tests use a local synthetic child process and real
  pipes, exercise one-megabyte stderr writes, invalid UTF-8 bytes, journal-lock
  independence, stderr read errors, and EOF/close behavior. The 24-test set
  also includes existing journal retirement, stdout EOF, process-tree cleanup,
  and UTF-8 controls. No GUI or app-server executable is started.
- **U — uncertainty:** this validates only the inert host-side contract. It
  does not establish behavior with the real app server, live GUI/model use,
  task effect, latency, efficiency, or cross-platform production readiness.
  GitHub's Ubuntu Native MCP check has not yet run on this successor. The
  original #7094 review descriptor requires two distinct nonauthor approvals;
  no GitHub APPROVED reviews are recorded and no prior votes transfer.

## Commands and outcomes

RED on current main (Python 3.14.5/macOS):

```sh
PYTHONPATH=research/live_control python3 -m unittest -v \
  research.live_control.test_appserver_stderr_drain_01a0ff2d
```

Result: 5 expected failures before the repair. An earlier invocation without
`PYTHONPATH` failed at import setup and is not counted as a test result.

GREEN target suite on the workflow-matched Python 3.12.13 environment, with
`research/live_control/requirements-native-mcp.txt` plus the workflow's exact
`Pillow==10.2.0`, `numpy==1.26.4`, and `python-xlib==0.33`:

```sh
PYTHONPATH=research/live_control PYTHONDONTWRITEBYTECODE=1 \
  /tmp/unjuno-7094-ci-venv-20261005/bin/python -m unittest -v \
  research.live_control.test_appserver_stderr_drain_01a0ff2d \
  research.live_control.test_appserver_journal_close_01a0ff2d \
  research.live_control.test_appserver_reader_retirement_01a0ff2d \
  research.live_control.test_app_server_eof_stop \
  research.live_control.test_appserver_process_tree_cleanup_20261004 \
  research.live_control.test_appserver_utf8_2d0b
```

Result: `Ran 24 tests ... OK`; the same command with `-O` also reports
`Ran 24 tests ... OK`. `git diff --check` and `git diff --cached --check`
passed before the integration commit.

The complete repository `runtime/integration_checks/native.py` runner was also
run on macOS 27.0.1 arm64. It is not green on this host: the successor ran 545
protocol tests (4 failures, 6 errors, 5 skips) and 205 harness tests (31
errors). To isolate attribution, the same pinned Python 3.12 environment and
runner were run against the exact base main commit. Baseline main ran 540
protocol tests with the same 4 failures, 6 errors, and 5 skips, and the same
205 harness tests with the same 31 errors. The sorted failing/erroring test
identifiers match exactly; the successor's five added stderr tests all pass.
The observed issues include Linux `/proc/self/ns/pid` assumptions and existing
host-path-sensitive checks. Therefore the broad macOS runner is recorded as a
baseline host failure, not as a PASS and not as a regression introduced by
this successor. Full logs and runner JSON remain in the local temporary
directories `/tmp/unjuno-7094-native-py312-currentmain-20261005` and
`/tmp/unjuno-7094-native-baseline-py312-currentmain-20261005`.

Container attempt: OrbStack 2.1.3 / Docker 29.4.0 is running, but
`docker image inspect python:3.12-slim` stopped with `operation not supported`
while reading a containerd content-store blob. No container test was run and
no image/cache pruning or repair was attempted. This is an infrastructure
`STOP`; the hosted Ubuntu CI remains the platform-appropriate next gate.

## Integration and retention decision

- Original PR #7094 remains unchanged, Draft, and unapproved. This successor
  does not transfer its proposal, review votes, or application authorization.
- Open PR #7125 records exact predecessor `e7f71d63405e1fdd20580fe8f3a893081ecbc94b`
  as a dependency. Keep the original #7094 branch and PR until that dependent
  review lineage is explicitly reconciled.
- No main merge and no remote branch deletion were performed. Do not merge this
  successor until its hosted checks and fresh independent review/application
  gates pass.

## Latest-main refresh — 2026-10-05

Before publication, `git ls-remote` showed main had advanced to
`9febfe4926cde6629f9751d6444f6b802cf31328`. A targeted diff from the initial
base to this main found no changes to the five inherited source/test/runner
paths. The successor was then merged with this exact main commit; refresh head
is `dc81a29a7d1aed0133f12a53e89787d35fae7f0f`, with parents
`4c5dc77d804055009f9f6e53b7362ae3925d66f2` and
`9febfe4926cde6629f9751d6444f6b802cf31328`.

After that sync, the same six-module target command passed `24/24` normally and
`24/24` under `python -O` on CPython 3.12.13. The complete local native runner
was not rerun on this refreshed tree; the detailed macOS baseline comparison
above is specifically against the earlier `1fa854d` checkpoint. The hosted
Ubuntu Native MCP check remains pending on the successor.

## Latest-main refresh — 2026-10-05 (publication checkpoint)

Before publication, live main advanced again to
`cd3a410a930e5f1e29a22cee36d9a149fbc106c7`. The diff from the previous main
`9febfe4926cde6629f9751d6444f6b802cf31328` contains 62 paths, all outside the
six paths changed by this successor. The exact latest main commit was merged
into this rescue branch (see merge commit in Git history). On the merged tree,
the six targeted modules passed `24/24` on CPython 3.12.13 both normally and
under `python -O`. The full native runner was not rerun on this newest
checkpoint, and hosted Ubuntu CI/review are still required. A preliminary
`pytest` invocation was unavailable because pytest is not installed in the
workflow-matched environment; the repository's documented `unittest` command
was used successfully instead.
