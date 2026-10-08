# #1906 typed claim-sink cut-set transfer A2 — formal result

Decision: **`PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED`**.

This is a static, source-bound successor to #1893. #1893 remains an immutable harness stop and is not pooled. No #827 X11/live case was rerun.

## Exact source facts

The retained #827 source establishes one explicit ordering:

`release verification → optional local journal/fsync → ordinary receipt-pipe attempt`.

The retained parent case runner separately establishes:

`ordinary recovery/drain → data_recovery_ns → journal read → candidate recovered publication`.

Formal source anchors were unique:
- watchdog lines: 19, 26, 28, 29, 30, 32;
- run_case lines: 65, 68, 72, 73, 75, 76.

## Typed sink classifications

1. **RELEASE_VERIFIED vs post-release data/evidence vertices**
   - base reachable: true
   - arbitrary declared DATA failures: true
   - minimum DATA-only cut: none.

2. **DURABLE_LOCAL_RECEIPT vs ordinary pipe/recovery**
   - base reachable: true
   - arbitrary ordinary-pipe/recovery failures: true
   - minimum DATA-only cut: none.

3. **DURABLE_LOCAL_RECEIPT when local journal is also a fault domain**
   - base reachable: true
   - arbitrary declared evidence-storage failures: false
   - minimum DATA-only cut: 1.

4. **REPUBLISHED_RECEIPT vs ordinary recovery phase**
   - base reachable: true
   - arbitrary recovery-phase failure: false
   - minimum DATA-only cut: 1.

5. **PIPE_ONLY local evidence sink**
   - base reachable: false
   - minimum DATA-only cut: 0.

Every classification matched the independent direct-reachability oracle and the #1882 cut-set theorem.

## Controls and integrity

All four source-order/scope corruptions were rejected:
- ordinary pipe moved before release verification;
- release verification moved after journal completion;
- recovered-publication block moved before recovery;
- A2 wrapper changed from framing-only repair to watchdog-source substitution.

Independent audit: PASS, errors [].

Formal invocation1; reruns0; replacements0; tuning0; X11/live reruns0.

Result SHA-256: `ccb88222cd4679cc204752c97eb0aa79888e69cec85e5fb64a0879baef69526a`.
Audit SHA-256: `4209b65f1a778f904d4537a9a5eba10782877ca981f8a1e2d76905ba85fe0740`.

## Interpretation

The phrase “safety plane is independent of the data plane” is too coarse unless the claim identifies both its **sink** and **fault set**.

For exact #827 source, physical release verification is structurally upstream of local journal and ordinary receipt-pipe work. The journal-backed durable receipt is also structurally independent of the ordinary pipe/recovery domain. But it is not independent of its own journal/filesystem dependency, and the parent-level republished receipt is created only after the ordinary recovery/drain phase.

Therefore #827 supports:
- release despite the retained temporary ordinary-data backpressure;
- post-release durable local evidence across that ordinary-pipe block;
- later recovery after unblock.

It does **not**, from this source alone, establish that republished evidence remains reachable if the recovery phase is permanently unavailable.

## Limits

This result is exact only for the explicit retained Python control flow and declared graph edges. Hidden dependencies in Python libraries, process scheduling, kernel/X-server behavior, filesystem semantics, hardware and deadlines are outside the proof. It is not a hard-real-time, physical-device, cross-platform or production-safety claim.
