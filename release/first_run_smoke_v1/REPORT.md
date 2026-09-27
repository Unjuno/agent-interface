# First-run launcher repair — retained result

**Disposition: PASS_SCOPED_LAUNCHER_REPAIR.**

This is an executed offline release-boundary experiment, not a new GUI/model
benchmark. The product's full installation and capability gates remain open.

## Provenance

- Task: PH48-FIRST-RUN-SMOKE-20260915-01; coordination in Issue #60.
- Immutable BASE: `ff2bbb5e200e2bf8ee2295ad97ca9dd0f158a371`.
- Frozen source/plan: `d9e031c665f63b3740abac876b77da5134a065af`.
- Branch: `release/first-run-smoke-ff2bbb5`.
- Result: `results/first-run-smoke-20260915-01/`; no retry of this result ID.
- All four materialized upstream files match their Git blob IDs. All five
  added source/plan/document files also match the published freeze-tree blobs.
- The two runtime changes are only Git modes `100644` to `100755`. Neither
  script content, runtime Python nor a frozen scientific result was changed.

## Executed comparison

| Condition | Setup v3 | Launcher v3 with doctor |
| --- | --- | --- |
| BASE mode 0644 | EACCES, bash exit 126; zero dispatch | EACCES, bash exit 126; zero dispatch |
| Same bytes, mode 0755 | Expected venv/pip/doctor dispatch; exit 0 | Expected doctor dispatch; exit 0 |

The dispatch destination was a **fail-closed test double**. No real venv/pip,
package installation, doctor, display or model ran. Real POSIX exec and bash did
run. The comparison changes only filesystem executable mode; both controls and
candidates use the same source bytes and double.

The source-frozen test suite ran **21 tests, zero failures, zero errors, zero
skips**. It covers argument preservation, paths containing spaces, a foreign
working directory, venv preference/fallback, missing Python, all three setup
failure stages, CRLF, missing/symlink files, malformed/duplicate pins, Python
syntax, committed versus worktree permissions, modified worktree bytes, and
refusal to overwrite retained reports.

The separate preflight run passes as **archive_filesystem_only**. The working
container was not a full Git checkout: GitHub DNS failed, and selected exact
files were materialized through the GitHub connector. Committed-mode behavior
was tested in disposable local Git repositories, not mislabelled as a full
project clone test.

Environment: Linux 6.18.44 x86_64, glibc 2.41, Python 3.13.5, five visible logical
CPUs; one serial matrix, no model batches. Clocks were uncontrolled. Test elapsed
time is diagnostic only; no latency/throughput or Python-3.13 runtime dependency
compatibility is claimed.

## Concurrent-agent check

At independently reread main `56eeda0dd3368c24bb4589d547489bbfbf6c1b69`, the
runtime subtree remained `9c15c48a3bf84c8fb7ac23926363cfe2669a413e` and release
subtree remained `91b6fdbe53e1edfd8b29617dfeaaea5fbb8f224f`, both equal to BASE.
Thus no overlapping runtime or release changes were observed at that snapshot.
The source-freeze SHA had zero Actions runs in the subsequent API read. Main
was not rebased, overwritten or advanced by this task. Recheck at merge time;
this is a snapshot, not a lock on future changes.

## Limits and next acceptance boundary

This closes the documented POSIX entrypoint permission defect only. It does not
close real setup/doctor, compatible wheels, model bridge, full dependency closure,
fresh golden GUI success, native Windows/macOS, DOOM recovery benefit, MAP01
clear, or general reliability. The remaining release-owner check is one isolated
real installation/doctor and separately authorized user-like golden run on the
actually claimed host, with independent output/release audit and an exact
runnable artifact. Do not substitute this test-double result for that evidence.

## Reproduce the static gate

```bash
python3 release/first_run_smoke_v1/preflight.py --root .
python3 -m unittest discover -s release/first_run_smoke_v1 -p 'test_*.py' -v
```

Keep the retained result directory read-only. A newly versioned engineering
replication must use a fresh output path; it is not the original first outcome.
