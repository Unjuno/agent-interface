# Construction record — Issue #5795 T0

Status: `PASS_PROTOCOL_UNIT_CHECKS_ONLY`. No candidate policy, SQLite crash
cutpoint, or formal row was run. Candidate count = 0; independent formal-auditor
count = 0. This file does not report a result for H.

## Frozen inputs

- Intake main: `ff2164a8b16d386571c91ebba19f6604b4776581`.
- Rebased main before formal execution: `8986380d8ec265f9cdc4a282fcd4ed93254acd49`.
- Branch: `research/crash-atomic-suppression-5795-t0-20261001`.
- Additive path: `research/experiments/crash_atomic_suppression_5789_t0/`.
- Protocol: `FREEZE.md`.
- Schedule and identity helper: `protocol.py`.
- Construction checks: `test_protocol.py`.

## Local checks

Command:

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0/protocol.py research/experiments/crash_atomic_suppression_5789_t0/test_protocol.py
git diff --check
python3 research/analysis/check_index.py
```

Result: 5/5 unit tests passed; `py_compile` passed; `git diff --check` passed;
analysis index passed with 272 retained result/failure directories on the first
run and 274 after main advanced; the final run passed at 274.
The first index invocation was an environment STOP because the checkout's
sparse patterns omitted `research/analysis/README.md`; the required read-only
paths were then materialized in this worktree and the unchanged checker passed.
No generated index file was edited.

These tests exercise only case-list uniqueness/coverage, deterministic source
schedule hashing, and candidate identity binding. They do not exercise storage,
subprocess recovery, any comparison arm, or the decision oracle. They are
construction checks and are excluded from every formal denominator.

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

## Formal allocation status

At the time of this record, Issue #5795 has no explicit isolated guest/daemon
assignment. Existing repository Obstac precedents use an OrbStack Docker
context, but that shared context is not treated as a dedicated guest. The
recent resource-queue state also contains an unassigned #5704 request followed
by a separate #59 request; neither grants resources to #5795. No Docker
context, daemon, guest, container, prior task-owned machine, or container
inventory was queried or touched.

Formal status: `NOT_STARTED_WAITING_FOR_EXPLICIT_ISOLATED_ALLOCATION` (no formal
STOPPED candidate attempt). Obstac's repository convention is understood as
OrbStack Docker plus frozen `OBSTAC_*` provenance values; there is no standalone
Obstac CLI/MCP exposed here. Use only the exact assigned isolated endpoint and
record runner/version configuration if the coordinator provides it.

## Next gate

Before any formal command: obtain explicit non-overlapping assignment for
Issue #5795 naming owner, time window, isolated guest/daemon and endpoint; then
recheck main, active branches/PRs/queue, output emptiness, pinned Linux/arm64
image identity, source/schedule/auditor hashes and bounded resources. Freeze
candidate and raw-only auditor first. Run candidate once; run the separate
auditor only if candidate exits zero. Preserve any failed gate as STOP with
candidate/auditor counts 0/0 and do not retry.
