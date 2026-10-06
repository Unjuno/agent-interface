# #6501: late cleanup can close a different FD lifetime

**Scoped method result: PASS_FD_LIFETIME_BOUNDARY_SCOPED.** In both deliberately
directed reuse schedules, two independent integer-FD cleanup sites closed the
replacement reader after correctly closing the original one. A shared one-time
ownership take preserved the replacement reader in both schedules. Both normal
data controls delivered D and the unrelated sentinel R. The integer-only
construction is unsafe in these two cells; the method PASS does not make it safe.

| Policy | Schedule | Late close target | Sentinel probe |
|---|---|---|---|
| integer_copies | caller close/reuse before worker finally | replacement pipe | EBADF9 |
| once_owner | caller close/reuse before worker finally | no second claimed FD | R |
| integer_copies | worker finally/reuse before late caller | replacement pipe | EBADF9 |
| once_owner | worker finally/reuse before late caller | no second claimed FD | R |
| integer_copies | normal completion | original pipe only | R |
| once_owner | normal completion | original pipe only | R |

Caller-first rows separately retain an important completion limit: closing the
original slot did not complete the old read. Even after the FD table referred
to the replacement pipe and R was queued there, the native worker still showed
Linux read63/stateS/anon_pipe_read on the same numeric slot. Only the later
harness D write to the original pipe released that read, which returned D.
The old read's kernel description and the new FD-table object's identity are
different. Harness release is cleanup and never counted as cancellation success.
Worker-first rows join the native worker before reuse and late caller cleanup.

## Execution and custody

- New allocation6501-FD-LIFETIME-ORBSTACK-A01-20261003-01a0ff52-70ab, claim5965896256,
  prospective remote freeze5966020614. Source08806ad5acb40a7533cf75fb6c4e3fc8783b7826
  / FREEZE SHA7ae03262d285c38c65899e90e07cf52aafacc704ca23003b59a23d942c68a12d;
  all20 source/input pins unchanged after execution and at the guest source.
- Cached imagepython@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016;
  CPython3.12.15/aarch64, Linux7.0.5-orbstack-00330-ge3df4e19b0a0-dirty. Selected
  executable/threading hashes and actual cgroup25000/100000 CPU/134217728B memory
  match the frozen environment. Readonly source/root, networknone,pids32,pullnever.
- Exactly one producer and one independently structured raw-only ledger auditor;
  exits0/0, retries0. Host attached05:38:26.919863–05:38:30.441474UTC. Candidate
 05:38:27.573636–05:38:29.173372; auditor05:38:29.174099–05:38:30.280356. Times
  describe execution receipts, not a matched latency/efficiency experiment.
- Six rows/134 events, original22208-byte raw SHA256
  `2aa2e68964107448392c957621bac4b4b747dc3a324aed45c4477e6c1221176d`.
  All seven guest_output.tar members match their original byte streams. The
  auditor imports neither candidate nor ownership and reconstructs typed role,
  inode/device/alias/FD ledger, write/read/close order, native blocked witnesses,
  primary probes and final closed resources/native-thread absence. Zero errors.
- Eight effective copied-data faults are refused after a separately passing
  saved-data baseline. This ordinary retained-data check on host CPython3.14.5
  invokes no original producer or primary formal-auditor allocation. Ordinary
  ownership construction2/2 and AST9-file checks preceded freeze.
- All six final ledgers are closed and all native reader TIDs absent. The owned
  container is exited0/Pid0/noOOM; source/raw/image/container retained. The
  dedicated guest is subsequently stopped, with a separate release receipt.

## Preparation failure is retained

The first normal source commit began a94,895-object partial-clone lazy fetch.
The author incorrectly started the own-branch push before that commit completed,
so only source base9c26e20 was published. Producer/auditor counts were0/0. The
verified own commit/fetch tree was terminated; commit exited143. From the
unchanged full-base index, write-tree--missing-ok/commit-tree/update-ref created
08806ad5, preserving every base path and adding exactly21 source files. A normal
forward own-branch push and remote readback established exact08806 before the
prospective freeze comment and first formal execution. This is a preparation
repair, not a scientific retry or erased outcome. Private process-stop evidence
and public hostname-redacted derivative hashes remain linked.

## Decision and limits

REJECT integer-only independent caller/finalizer closure for the tested reuse
schedules. REQUIRE one closure authority for the original lifetime before
composing cancellation with a blocking verification read. A shared one-time
take is sufficient here; keeping closure entirely at the worker with a separate
control channel is another simple sufficient ownership design. No production
mechanism is required or deployed by this archive.

The actual reuse is intentionally forced by dup2 after a vacated slot and uses
an already-created private sentinel pipe. It measures deterministic boundary
behavior, not natural race frequency, performance or general reliability. The
same shared owner object is crucial; independent owner copies/resetting its FD
would not satisfy the construction. No arbitrary I/O preemption, close-error/
EINTR retry, hostile telemetry, descriptor exhaustion, signal-handler races,
uncooperative concurrent closers, socket/macOS/Windows behavior, GUI/effect/
currentness/authority/input release/workload/throughput/adoption is established.
Original #6915/#6890 and co-ready #6927 allocations were not replayed.

This author-written raw-only ledger is procedural/algorithmic separation, with
common Python/OS telemetry assumptions. Independent nonauthor content review,
exact-current combined tree, actual platform requirements and uniquely owned
expected-old application remain separate gates. #6501 remains open.

## Evidence access

[PLAN](PLAN.md), [FREEZE](FREEZE.json), [raw](results/raw.jsonl),
[first audit](results/audit.json), [driver receipts](results/driver_receipts.json),
[custody](results/CUSTODY.json), [copied controls](results/copied-controls/summary.json),
[release](results/resource_release.json), [preparation provenance](PUBLICATION.json),
[byte manifest](SHA256SUMS).

Source snapshots/tests are excluded from automatic pytest collection. Run the
ordinary ownership tests explicitly with `python3 -B -m unittest
test_construction -v`. Raw-only re-audit may use a fresh scratch output; do not
invoke launch_once/candidate on the consumed allocation or overwrite first raw.

Primary OS contracts are [Linux close(2)](https://man7.org/linux/man-pages/man2/close.2.html)
and [dup(2)](https://man7.org/linux/man-pages/man2/dup.2.html), read2026-10-03.
The documented FD/open-description distinction motivated this experiment;
the local measurement and its limited decision are separately retained here.
