# F03 independent saved-row audit construction

Status: PASS_CONSTRUCTION_ONLY. Formal native allocation 0; official auditor allocation 0.

Source commit: `16a610833`. Git archive SHA256:
`d50d6bd42b0f219551460a86e7ca4173c769c3b425beaeb5426942b8883ae231`.
Host, guest and in-container archive digests matched before execution.

Owned VM: research-6183-t0-20261003. Container: f03-audit-construction-v1.
Image: sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Engine State: StartedAt 2026-10-03T23:21:38.801982592Z;
FinishedAt 2026-10-03T23:21:39.045485414Z; ExitCode 0; OOMKilled false.
Observed inside container: UID/GID 501; cpu.max 100000 100000;
memory.max 1073741824; memory.swap.max 0; pids.max 128.
Network none, read-only root/input archive, private tmpfs output.

Executed `python3 -B -O -W error -m unittest discover -v`:
3 tests passed, 0.001 seconds. Positive saved construction rows accepted;
bad clocks, missing handshake, wrong source, boolean-as-integer liveness,
missing/reordered/duplicate cells rejected. Host same three tests also passed.

This auditor does not call runner.expected and does not invoke the producer.
It checks row semantics, not full formal custody. Original construction JSON
is retained in RUNNER-CONSTRUCTION.log; original tmpfs files were not exported.
No consumed experiment was replayed. No current-controller adoption or gameplay
claim. Repository-wide suite was not run; qualification remains package-scoped.

Next gates: strengthen producer first-STOP controls, exact output inventory,
frozen execution/source delivery, independent prelaunch review, then a new
prospectively declared formal allocation and separate saved-result auditor.
