# Construction record — Issue #5846 successor T0

Status: `PASS_HOST_CONSTRUCTION_ONLY`; no formal candidate or auditor has run
for Issue #5846 (0/0). This is an additive successor to Issue #5795; the
predecessor allocation record and any result remain immutable.

## Frozen inputs and scope

- Successor Issue: #5846; parent idea: #5789.
- Branch: `research/crash-atomic-suppression-5846-t0-20261001`.
- Additive path: `research/experiments/crash_atomic_suppression_5789_t0_successor_5846/`.
- Preparation base: main `8f18bb65d75deaaafed8b4e6ebbd430371c1d05`; confirm current main again at the start gate.
- Protocol/schedule/candidate/auditor: `FREEZE.md`, `protocol.py`, `worker.py`, `runner.py`, `audit.py`.
- Launcher and host/guest output mapping: `container_runner.py`.

The frozen finite process-crash schedule has 15 rows. It tests toy policies A
(memory-only), B (split writes) and C (one SQLite transaction), with a separate
raw-only auditor. It tests only process SIGKILL/restart and deterministic
logical TTL/GC behavior, not power loss, physical compaction, multi-writer
serialization, a product runtime, GUI effects, or product safety. The H/T/D/C/U
and formal pass/fail/stop rules are in `FREEZE.md`.

## Predecessor STOP — preserved, not retried

Issue #5795's assigned one-shot allocation was
`crash-atomic-suppression-5795-t0-20261001-01`. Its exact launcher preflight
returned `STOP_FORMAL_ARGV_MISMATCH` before Docker candidate invocation;
candidate/auditor counts were 0/0. That STOP consumed the predecessor
allocation and remains unchanged in its original branch/Issue/PR. The successor
does not reinterpret it as candidate evidence and uses a new Issue, branch,
package path, guest, context, and allocation.

## Construction corrections and checks

The predecessor host/guest path mapping initially used the guest's
`Path(__file__).parent` as a host mount root, which is not valid when the
launcher executes inside the guest at `/study`. The successor now requires the
absolute host source root from the frozen runtime manifest and maps only paths
contained under `/study` to that explicit root. Host unit tests cover a valid
mapping, reject paths outside the assigned mount, and reject a relative host
root. This is orchestration construction evidence only.

The inherited host rehearsal exercised the 15-row matrix and independent audit
without a formal allocation. Its previous recorded result was 15/15 audited
rows, including the baseline failures; it is historical construction evidence,
not an Issue #5846 result. Earlier setup/test errors and their corrections are
retained in the predecessor Issue #5795 record rather than rewritten here.

Successor local check command (on source commit `552f4852e9a341a75a7281d908ef8712b022005d`):

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0_successor_5846 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0_successor_5846/*.py
git diff --check
python3 research/analysis/check_index.py
```

Result: 19/19 unit tests passed, `py_compile` passed, `git diff --check`
passed, and `research/analysis/check_index.py` passed with 291 retained
result/failure directories indexed. During construction, an early invocation
test initially failed because its mock did not model guest `/study` path
translation; after correcting the fixture, the full suite passed. One earlier
analysis-index check detected an unrelated pre-existing ordering-only
difference; the final checker passed on the rebased current main. Neither
construction event invoked a formal candidate or auditor. Do not represent
host rehearsal results as fresh formal evidence or denominator rows.

## Successor allocation gate

The directly user-authorized successor slot was recorded on coordination Issue
#5085: `crash-atomic-suppression-5846-t0-20261001-01`, 07:35–08:05 UTC. It
requires a new isolated ARM64 Ubuntu 24.04 guest `crash-atomic-5846-20261001`
(1 vCPU, 2 GiB memory, 16 GiB disk) and guest-local context
`crash-atomic-5846-local` at `unix:///var/run/docker.sock`. At the start gate,
recheck current main, active issues/PRs/branches/coordination leases, absence of
overlapping guests, the guest/context endpoint, pinned image digest/platform,
source and manifest hashes, host/guest mapping, empty output directories, and
resource limits. Any failed or ambiguous prerequisite is a terminal STOP for
this allocation with 0/0 candidate/auditor counts. If all gates pass, invoke
the candidate once and only invoke the independent auditor after candidate
exit 0. Stop the guest within the reserved slot. Preserve exact raw output,
logs, hashes, audit, and any STOP/FAIL; update Issue #5846 and its own PR.
