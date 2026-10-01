# Construction record — Issue #5795 T0

Status: `PASS_HOST_CONSTRUCTION_ONLY`. The complete 15-row process matrix and
separate raw-only auditor were exercised on the host as construction rehearsal.
These observations are excluded from the formal denominator and are not a
result for H. Formal candidate and formal auditor counts remain 0/0.

## Frozen inputs

- Intake main: `ff2164a8b16d386571c91ebba19f6604b4776581`.
- Rebased main before construction matrix: `49db21e330768800e8b3486203b70306f4e402f6` (rechecked before formal freeze; main can advance).
- Branch: `research/crash-atomic-suppression-5795-t0-20261001`.
- Additive path: `research/experiments/crash_atomic_suppression_5789_t0/`.
- Protocol: `FREEZE.md`.
- Schedule and identity helper: `protocol.py`.
- Candidate fixture: `worker.py`, `runner.py`.
- Independent raw-only construction auditor: `audit.py`.
- Construction checks: `test_protocol.py`, `test_execution.py`.
- Bounded container command builder and allocation gate: `container_runner.py`.

## Scope correction retained before formal execution

An independent review caught a scope mismatch: the initial `expiry_gc` case
only retired a row without advancing time or collecting expired state. Before
any formal row, the deterministic expiry/GC path was implemented: TTL
100→150, probes before expiry, after expiry/before GC, and after GC; pre-expiry
GC no-op; transactional logical GC at 150; and retained-tombstone inspection.
Physical database-file compaction remains out of scope. The host matrix rerun
below verifies the corrected schedule; no formal result exists to alter.

## Local checks

Command:

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0/*.py
git diff --check
python3 research/analysis/check_index.py
```

Result: 15/15 tests passed (5 protocol checks, two SIGKILL/child lifecycle
checks, one full 15-row host matrix plus separate auditor CLI, five
preflight/output-gate checks, two bounded container-command checks, and an
audit-container output-directory regression check); the
audit matched 15/15 frozen rows, including 10/10 policy-C rows and reproduced
the expected baseline failures. `py_compile` and `git diff --check` passed. Analysis index
passed with 285 retained result/failure directories on the latest checked main.
No generated index file was edited.

The full host rehearsal exercises subprocess SIGKILL boundaries, SQLite state,
the three toy policies, and a distinct raw-only auditor. It is still only local
construction evidence: not run in the assigned Linux/arm64 container, not the
formal Obstac candidate, and excluded from every formal denominator. Raw bytes
were held in an ephemeral temp directory and are not represented as a retained
formal result. Do not cite the host pass as evidence that the formal hypothesis
passed.

The corrected `expiry_gc_tombstone` row was independently inspected in the
host rehearsal: at fixture time 149, the suppression denied and pre-expiry GC
changed 0 rows while retaining the live row; at exact expiry 150, the
pre-GC probe returned UNKNOWN; GC changed 1 row to RETIRED with `retired_at=150`
and retained it; the post-GC probe returned DENY_RETIRED. The raw-only audit
matched all 15 rows, including 10/10 policy-C rows, with no errors. A negative
control that falsified `gc.retained` was rejected by the separate audit CLI.
This remains host-only construction evidence and was not added to any formal
denominator.

## Preserved construction-command errors

- Initial analysis-index check: `FileNotFoundError` for
  `research/analysis/README.md`, which the inherited sparse-checkout pattern had
  omitted. No source or index was changed by that attempt. Required read-only
  files were materialized in this worktree; the same checker then passed.
- One `py_compile` command used the misspelled path
  `crash_atomic_suppression_5795_t0/test_protocol.py`; Python returned
  `FileNotFoundError`. The five unit tests had already passed. The corrected
  py_compile command for the actual `..._5789_t0/test_protocol.py` passed.
- One SHA-256 collection command likewise used the wrong `..._5795_t0/` path
  and returned `shasum: No such file or directory`. Corrected hashes are
  recorded in `SHA256SUMS` after source freeze. No candidate or formal auditor
  was invoked by these commands.
- The first formal-gate source-drift test had a stale manifest digest, so it
  stopped at the earlier digest gate rather than testing source drift. After
  correcting the test input to carry the exact digest of its deliberately
  stale manifest, the intended source-hash STOP was observed and all 10 tests
  passed. No candidate row ran in either attempt.
- The container-command stub test initially omitted the manifest-specific
  command option and therefore did not expect the assigned endpoint/auditor
  hash environment fields. The caller was corrected; the test checks the exact
  endpoint and pinned invocation before any Docker process is spawned.
- The follow-up test fixture initially lacked a `docker_host` manifest field;
  its `KeyError` occurred while constructing the stub command, before any
  Docker invocation. The fixture now supplies a named fake endpoint and the
  command assertions pass without contacting it.
- The first audit-output migration treated a filename as a directory, and the
  missing-allocation launcher check attempted to read the not-yet-created
  freeze file before reporting the allocation STOP. The output contract is now
  an empty dedicated directory containing `audit.json`; the no-allocation gate
  runs before freeze loading. Neither failure launched Docker or a candidate.
- The construction-launcher mock first failed because its synthetic
  construction endpoint lived only in the child env dictionary, while the
  in-process `main()` correctly reads the current environment. The test now
  applies/restores those two fake values around the call; its Docker subprocess
  remains mocked and all endpoint assertions pass.
- The first host matrix after adding expiry columns stopped when the child SQL
  INSERT still supplied six values for the expanded row. The one row INSERT was
  corrected before further work; the complete matrix then passed. That STOP
  was host construction only, not a formal allocation outcome.
- A final Docker CLI review found `--context` and `--host` were being specified
  together. The launcher now uses the named context as the sole connection
  selector and first compares its local configured endpoint with the assigned
  endpoint; it does not query daemon state. The first mock run then omitted
  stdout for that new context-inspect process; after stubbing the JSON endpoint,
  all 14 tests passed. No Docker daemon/container was invoked.
- A later regression test exercised the actual auditor Docker argv assembly and
  caught a file-vs-directory `--out` mismatch. The launcher now mounts an empty
  report directory and passes `/work/out`; 15/15 host tests pass. This changed
  only orchestration, not the frozen candidate/auditor bytes.

## Formal allocation status

An explicit user-authorized allocation was recorded in coordination Issue
#5085: `crash-atomic-suppression-5795-t0-20261001-01`, 06:00–06:20 UTC, a new
ARM64 Ubuntu 24.04 OrbStack guest, 1 vCPU, 2 GiB memory, 16 GiB disk, isolated
from host and peer networking. A Docker daemon and named context were created
inside that guest only; endpoint `unix:///var/run/docker.sock`. The pinned
`python:3.12-slim` image was pulled and inspected in the guest as
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
(`linux/arm64`). Formal candidate/auditor have not yet been invoked.

## Next gate

Before formal invocation: recheck main, active branches/PRs/queue, endpoint,
image identity, source/schedule/auditor hashes, empty output paths and resource
limits. The in-container runner and host launcher compare source, schedule,
freeze digest and runtime identity against `FREEZE.json`. Run the candidate
once; run the separate auditor only if candidate exits zero. Preserve any
failed gate as STOP with candidate/auditor counts 0/0 and do not retry.
