# Construction record — Issue #5795 T0

Status: `PASS_HOST_CONSTRUCTION_ONLY`. The complete 15-row process matrix and
separate raw-only auditor were exercised on the host as construction rehearsal.
These observations are excluded from the formal denominator and are not a
result for H. Formal candidate and formal auditor counts remain 0/0.

## Frozen inputs

- Intake main: `ff2164a8b16d386571c91ebba19f6604b4776581`.
- Rebased main before construction matrix: `2a69173110856607c02e5213561679938c5988e3`.
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

Result: 14/14 tests passed (5 protocol checks, two SIGKILL/child lifecycle
checks, one full 15-row host matrix plus separate auditor CLI, five
preflight/output-gate checks, and two bounded container-command checks); the
audit matched 15/15 frozen rows, including 10/10 policy-C rows and reproduced
the expected baseline failures. `py_compile` and `git diff --check` passed. Analysis index
passed with 274 retained result/failure directories on the latest checked main.
The first index invocation was an environment STOP because the checkout's
sparse patterns omitted `research/analysis/README.md`; the required read-only
paths were then materialized in this worktree and the unchanged checker passed.
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

## Formal allocation status

At the latest recheck, Issue #5795 has no explicit isolated guest/daemon
assignment. Queue requests for #5776 and #5803 are not grants to #5795. The
proposed 07:35–08:05 UTC window is also only a request, not a lease. The
`FREEZE.json` endpoint/runtime manifest is intentionally absent until an
explicit grant provides real context and daemon endpoint; therefore formal
mode refuses before Docker. Existing
repository Obstac precedents use an OrbStack Docker context, but that shared
context is not treated as a dedicated guest. No Docker context, daemon, guest,
container, prior task-owned machine, or container inventory was queried or
touched.

Formal status: `NOT_STARTED_WAITING_FOR_EXPLICIT_ISOLATED_ALLOCATION` (no formal
STOPPED candidate attempt). Obstac's repository convention is understood as
OrbStack Docker plus frozen `OBSTAC_*` provenance values; there is no standalone
Obstac CLI/MCP exposed here. Use only the exact assigned isolated endpoint and
record runner/version configuration if the coordinator provides it.

## Next gate

Before any formal command: obtain explicit non-overlapping assignment for
Issue #5795 naming owner, time window, isolated guest/daemon and endpoint; then
recheck main, active branches/PRs/queue, output emptiness, pinned Linux/arm64
image identity, source/schedule/auditor hashes and bounded resources. The
in-container runner now compares source, schedule, freeze digest and runtime
identity against `FREEZE.json` before entering the row loop. A local outer
launcher still must invoke the candidate and auditor only through the exact
assigned endpoint with read-only source, no network, bounded resources and
separate output mounts; implement and mock-test that launcher before requesting
formal execution. Then run candidate once; run the separate auditor only if
candidate exits zero. Preserve any failed gate as STOP with candidate/auditor
counts 0/0 and do not retry.
