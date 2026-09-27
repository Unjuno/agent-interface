# Issue #3987: joined IPC completion evidence

**PASS_IPC_COMPLETION_JOIN_SCOPED — evidence-only, no runtime promotion.**
Successor to closed #2818; #2789, #3924/#3926 and global ROADMAP remain open.

## Executed result

One publicly hash-frozen local subprocess allocation completed24/24 fresh
streams. The exact current client (blob b2a3eeb6712f30dbdc5918a451a56f14096f5f65)
returned22 successful process results and2 partial-JSON failures;20 successful
results lacked valid joined initial completion under the declared contract.
These were controlled file-publisher fixtures, not20 real failed model calls.

Candidate final collection:6 available,2 pending,14 refused,2 transport holds.
Four delayed results were recovered without a second request. Every stream
retained one unchanged request.48 read-only collections include8 available
responses for6 distinct streams because2 stable results were read twice.
No input/dispatch authority was granted. Fixed usage7/2 is synthetic data,
not actual model token consumption.

Independent raw-only audit:1187 checks, errors=[],12/12 corruption controls
rejected,8/8 frozen sources unchanged.15 construction unit methods pass.
All24 client and24 publisher processes reaped without forced cleanup; all48
collector process exits retained. Formal invocations1; reruns0; model/broker/
GUI/task-input calls0. FORMAL.exit and AUDIT.exit are0, their stderr files empty.

## Exact publication

Ten base64 text fragments reconstruct one50,020-byte XZ archive (SHA256
4497871e6f98af11abdc61b17eddbb0fa5d844f2d6115605691836dc4af9d23b).
It preserves353 files /944,055 expanded bytes: full source,3 excluded
construction streams, every formal request/response/receipt/seal and phase
snapshot, process commands/outputs/exits, source freeze, auditor/tests,
raw-only audit, report and per-file hashes. Only generated Python cache files
are excluded. collector.py is also directly reviewable; SUMMARY.json retains
the exact auditor output.

Formal RAW SHA256:
da549496ad85bbc96d22e817dc1b8a22224cbc3f2b1452cbb35b2315ae01ae30

Source FREEZE SHA256:
b7bed0c33c5cfe046eafc7f8485c7adbfb8fb39e1523c24261965e24764cff4f

Preformal public source/gate freeze: #3987 comment5766718094.
First outcome: #3987 comment5766730795.
Intake main b2457b746a6df06f6536585dfe2ab937aff639f4. Preformal main advanced to
1c817de45cf944d144d76e288823b63bc0ec73a4; the target client blob was unchanged.

## Review without executing an allocation

Use a new extraction destination:

```sh
python -S unpack.py /tmp/issue3987-review
cd /tmp/issue3987-review
python -B -S -m unittest -v test_collector
python -B -S audit.py formal-01/RAW.json --controls
```

Extraction checks each fragment, complete archive, member inventory and every
member digest before writing; refuses existing paths and executes no study.
Do NOT rerun run.py with the consumed formal identity. A replication requires
its own source/plan/environment freeze and fresh allocation.

## H/T/D/C/U and limits

H: response-file existence/cardinality does not establish joined completion.
T: unchanged client, synthetic cooperative publisher, two read-only collection
phases, twelve frozen cases with two fresh repetitions; exact bytes/actor exits.
D: all24 rows, verdicts, request counts, byte/process/source gates and audit pass.
C: the seal is a NEW publisher contract. Existing main broker does not emit it;
prior replay supervisor uses another schema. No silent compatibility assumption.
U: real broker provenance, model response/usage, concurrent mutation, crash/power
loss, pinned Docker/OrbStack transfer and end-to-end task benefit remain unknown.

A nonzero broker-process field remains HOLD even with a zero child field; the
parallel zero-exit bug is not bypassed. Collector CLI exit0 means collection
returned a typed status, not that the result or task succeeded. Hash binding
is not authentication, semantic task success or a multi-file atomic snapshot.
The candidate assumes trusted private files and stable publication while read.
It is not a deployed drop-in repair or a general exactly-once protocol.

Actual runtime: provided Linux6.18.44/x86_64 execution container, CPython3.13.5,
stdlib, sanitized child environment. Docker CLI/image identity unavailable:
STOP_PINNED_CONTAINER_UNAVAILABLE. No Docker/OrbStack equivalence, real-model,
latency/token/cost or integrated desktop claim. Hardware/clock details and the
variable/unit table are in the packed ENVIRONMENT.json / PLAN.md.

Two outer tool calls displayed a terminal-clear/TERM diagnostic not present in
the actual study/auditor stderr files. The surfaced text is preserved separately
as an unlocalized tool-transport diagnostic; no trial was retried or erased.

The prior chat replay archive remains unchanged and locally available. Its1213
manifest files/10 sources revalidate and2341-check audit JSON equals the old
result. Only those posthoc verification receipts are included here, NOT that
previous full raw archive. Its old publication STOP remains historical.

All changes are confined to this additive research path. No shared runtime,
root README/CURRENT_GOAL/ROADMAP, predecessor artifacts or other branches change.
The next decision is explicit compatibility with a genuine sealed completion
producer; this experiment does not authorize model invocation or task replay.
