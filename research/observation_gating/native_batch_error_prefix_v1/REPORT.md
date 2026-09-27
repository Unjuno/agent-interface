# Native batch error-prefix study — Issue #4055

## Decision

PASS_NATIVE_BATCH_PREFIX_ERROR_BOUNDARY_SCOPED for the prospective48-case private local socket allocation. The legacy result API remains FAIL_UNREPORTED_CONSUMED_PREFIX. This is research evidence, not production promotion, semantic frame validation or a task-performance claim. The older32-case receive/hash experiment remains HOLD_CUE_INTEGRITY and was not rerun.

| Policy | Cases | Sent datagrams | Normal data written by native receive | Exposed to caller | Consumed normal data not exposed | Oversize errors | Independently observed unread |
|---|---:|---:|---:|---:|---:|---:|---:|
| Exact legacy |24|63|45|30|15 (9 cases)|15|3|
| Separate prefix/error |24|63|45|45|0|15|3|

These are directed finite counts, not failure rates. In MIDDLE [A,X,B], legacy raises on X without returning already consumed A, then a second read returns B. In LAST [A,B,X], neither A nor B returns to the legacy caller. In DOUBLE [A,X,B,X,C], both calls raise and C remains unread. The new API preserves the consumed A/B prefix while separately reporting size errors. It does not return X, restore X, replay any send, or credit unread C as delivered.

A zero-length datagram is retained as one transport item, not treated as stream EOF. Exact8192-byte input is accepted at the transport-size boundary. Neither implies a valid image/schema/current observation. Polling and count limits are unchanged; no speedup is measured here.

## H / T / D / C / U

H: a scalar error return after successful native reads can hide irreversible consumed progress. A structured partial-result contract should preserve that progress plus failure.
T:8 queued input schedules x2 policies x3 repetitions;48 fresh AF_UNIX/SOCK_DGRAM pairs,48 fresh exec consumers, exactly2 reads per consumer,3 immutable16-case batches. The parent queues identical synthetic bytes before launching each consumer and independently drains the socket afterward. Candidate receives only mode and FD, not scenario/expected outcomes. Exact source, allocation, schedule and decisions were publicly hash-committed before batch0.
D: all48 planned cases, all3 observed external exits0, all48 actual worker exits0, stderr empty; all17 frozen files unchanged. Independent raw-only auditor errors=[];14/14 copied-formal-evidence controls reject after mirroring modified decoded worker fields back into raw stdout.18 unit methods pass. No retry/replacement/pooling, postfreeze source edits or favourable case selection.
C: prequeued local datagrams, small bounded workload, cooperative malformed producer. Original receiver.py and receive_batch.c are exact copies; a newly compiled binary is used. The new ABI carries count and error separately. Diagnostic sentinel initialization changes unused output-buffer contents only; native-written prefix evidence is not retroactively credited as legacy caller delivery. No concurrent send/close, arbitrary errno, signal, FD misuse, denial-of-service or security exploitation is studied.
U: no GUI/input/model/provider/external-network experiment, user data, true observation freshness, semantic validity, general history completeness, cross-platform, task utility, cost/latency or product claim. Same-author separate auditor is not external human review. No calibrated timing uncertainty or population confidence interval is claimed.

## Source and chronology

Intake main6e5a6dd60cd93aee300cd4bd11712bb9d6bd8520. Only research/observation_gating/native_batch_error_prefix_v1/ is added on research/native-batch-error-prefix-20260922-a55f. Existing README/CURRENT_GOAL/ROADMAP/runtime/workflows and other worker branches are unchanged.

The source C/Python wrapper came from the exact retained old ZIP a55fed37ce2d65e132577aa9c1f754f8229524faf3ccf5eb4413000f368afa74, internal x11_receive_hash_handoff_allocation04 namespace. Their SHA256 values are c30bd022ec551f5d89b41b8657fa066aeb4883d80591527c927ae2e5d32a6439 and d311c1849d849b2c7c6cd248676045e171d5e0a060c241828e54dc1c5c3fb745. This is not the parallel AMD receive/hash branch. Full older raw archive publication remains outstanding; this new evidence bundle does not claim to include it.

Public source-hash commitment/readback: commit5bfd360398b31f93dcba7a3f670edbb4b4076757, PREMEASUREMENT.md blobe77274bd761f78fb1b2001f3c6bb416334ee9fc0. FREEZE.json SHA25627b099296dd396149eaa32db4da8f0502a7f26e939f0b0c27f00eb3948681085. Full source bytes were local then and are delivered afterward, not falsely described as previously public. First formal outcome is Issue#4055 comment5768713384.

Raw batch hashes:0=3e55b2df8019a2bb9e25d0dbc593da31b62988e26d6e6c149180b178fab714f5;1=cf46f7026719a170ffea05fd99d861aac5a7cad86a999538b6e8654885071cd6;2=4743f4a118d7881b29707561b77959b8b33a4a394bb7a845b97421b99f57b56d. AUDIT.json SHA25655012209b2fe02e57e84081e8be4af72f24386143483f56de307286e1dafd532. CONTROLS.json SHA256316772ad38f81a09a9c77a9cfebf738ca7795533ecd58ef0f43e209c4e1cabe2.

## Retained construction and implementation assumptions

Construction01 has two EMPTY rows and STOP: candidate child printed a complete response but was killed after the1s child wait, actual exit-9. No successful exit is inferred. Before freeze, adding -S to child and batch commands removed unnecessary site initialization; construction02 then completed16 cases. This observation does not prove why the first child exceeded its bound. Original raw/source snapshots and all logs remain unchanged in the bundle.

Python -B prevents cache writes, not cache reads. A protocol.py bytecode cache was created during schedule freezing and not independently listed in the preformal freeze. BYTECODE_NOTE.json records a postformal comparison: its decoded code equals compilation of the frozen protocol.py. The cache is retained. Individual historical import source/cache paths were not instrumented. This is a disclosed provenance limitation, not evidence of different executed protocol semantics.

Actual environment: Linux6.18.44 x86_64 execution container; Intel Xeon Platinum8573C guest, Python3.13.5/glibc2.41, installed gcc14.2.0. No Docker/OrbStack engine/image attestation. Frequency/host load were not pinned; time values are diagnostic only. Native int/uint64/pointer ABI and library/interpreter hashes are in frozen source/environment. No package installation. The20ms poll and2ms drain are inherited operational settings, not performance guarantees.

## Interpretation and conditional argument

Normal recv operations consume datagrams from this single-owner socket. A later size error cannot roll them back. Returning only that error hides earlier progress from the wrapper, and rereading the same socket cannot recreate the consumed data. The partial-result API returns exactly the already-written length slots, with the error in another field. Stable buffer ownership until copying is required. See PLAN.md for the complete argument, quantity/type/unit table and boundaries. Linux recv(2) documents real datagram length with MSG_TRUNC and zero-sized datagrams; no novel kernel defect is asserted.

For integration, treat consumed prefix, rejected item, unread suffix and caller-visible data as different facts. An error must not be interpreted as zero progress or permission to repeat an action. This result is a prerequisite/constraint on the proposed observation transport, not a drop-in runtime implementation or completion of#2117/#2789.

## Offline review

The new bundle includes complete source, binary, construction failures, raw sent/returned/diagnostic/unread bytes, stdout/stderr, external exits, freezes and audits. Its unpacker validates bounds and hashes and never runs experiment code. To validate a fresh extracted directory:

```
python -S -B audit.py . --out /tmp/new-prefix-audit.json
python -S -B controls.py . --formal --out /tmp/new-prefix-controls.json
python -S -B -W error::ResourceWarning -m unittest -v test_audit
```

Do not execute consumed invoke.py/run.py allocations. Re-auditing bytes does not send datagrams or load the native test binaries. Repository-wide CI and independent reviewer status are separate gates from these local results.
