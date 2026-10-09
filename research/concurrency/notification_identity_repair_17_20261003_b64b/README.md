# Exact notification identity repair (#17)

A callback may reenter wait_notification through the same public client and
consume the selected object. Mutable-deque enumeration then duplicates that
object and deletes an unrelated notification, or raises RuntimeError.
The repair snapshots references while retaining the existing Condition,
skips objects no longer queued, and removes a matching live object by identity
only after callback truth conversion. No outside-lock retry loop is introduced.
Other module ASTs, EOF ordering, close behavior and public signatures are unchanged.

H/T/D: exact conservation through nested public consumption; write ten
constructor-free deterministic regressions BEFORE modifying source, require
them and four existing EOF/queued-reply regressions to pass. C/U: directed
adversarial callable, not observed production incidence. Known normal callers
are pure. Blocking/unbounded recursive callbacks and #7003 reader starvation
remain. Snapshot adds O(n) references; identity membership can cost O(n²) per
full scan. No latency/resource improvement or whole-call recovery is claimed.
This does not adopt the #7003/#7029 outside-lock comparators.

Baseline:10 tests,3 failures/2 deque-mutation errors; PID4950 at2026-10-03
13:53:45UTC,exit1. First candidate launcher failed BEFORE child creation:
source/output directory collision, preserved launcher/failure. Corrected
launcher uses separate output; candidate PID5504 at13:54:12UTC passes10/10,
exit0. Relevant client discovery PID6073 at13:55:34UTC passes14/14,exit0,
including existing EOF fixtures with inert process streams and four actual
short reader threads which all retired. Homebrew CPython3.14.5/macOS, real
deque/Condition/RLock, rich Unicode nested params. No server subprocess/native
peer/model/GUI/task/input/release/OS timing/formal allocation executed. Own VM
stayed stopped. Historical7003/7029/7058 allocations/raw stay immutable.

Whole repository suite/hostedCI UNVERIFIED. This partial research repository
has independently frozen formal workflows and no root pyproject/Makefile test
entry point; indiscriminate execution crosses consumed allocation boundaries.
Selected workflow definitions inspected: no general client test/lint command
found. Syntax/whitespace and relevant14-test discovery are local validation.
Skill whole-suite advice does not authorize replaying historical allocations.

Reproduce the focused suite from root:
`PYTHONPATH=research/live_control python3 -B -m unittest discover -s research/live_control -p 'test_*app_server*.py' -v`
New test matches that pattern. Ten-test-only reproduction:
`PYTHONPATH=research/live_control python3 -B -m unittest discover -s research/live_control -p 'test_codex_app_server_notification_identity.py' -v`.
Raw unittest streams/receipts and first failures remain here.

Worker01a0ff52-b64b /FINAL-v5/ordinary17-NOTIFICATION-IDENTITY-R01/claim5969817860.
Source mainf474970f82d68b6648aac64f99048ad0c2fd5732,6508B clientSHA256
2290f2f8b3d2693db7358cbfe6fca4daf0553e8e2cec9ebcf88db533352c0abb.
Change:one client method,one regression file,this additive inert evidence.
No workflow/sharedindex/nav change. Main sends0. Genuine fixed nonauthor
quorum/current full-tree applicability certificate and sole fresh expected-old
forward main sender remain separate. Broad computer-control goalACTIVE.
