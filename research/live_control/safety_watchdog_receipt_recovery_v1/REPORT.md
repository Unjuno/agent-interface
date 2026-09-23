# Safety watchdog cleanup-receipt recovery — retained result

Task `SAFETY-WATCHDOG-RECEIPT-RECOVERY-20260917-002`, Issue #827.

## Decision

**`PASS_WATCHDOG_RECEIPT_RECOVERY_SCOPED`**, with the original frozen post-measurement auditor failure retained and a one-line read-only `audit_v2.py` correction documented separately.

A1 is separately retained `STOPPED_FORMAL_HARNESS_OUTPUT_FRAMING`; none of its partial material is pooled. A2 uses eight fresh IDs and changes only watchdog stdout framing parsing.

## A2 first outcome

Eight fresh X11 sessions completed in one formal block; reruns/replacements **0**.

- `pipe_only` 4/4: watchdog physically released F8 after owner SIGKILL, ordinary receipt pipe remained blocked, no journal row and no recovered cleanup receipt.
- `watchdog_journal` 4/4: same physical release and same blocked ordinary pipe, exactly one journal row and exactly one recovered cleanup receipt after data recovery.
- app-observed F8 press/release exactly once: **8/8**.
- terminal key up and measurement-boundary key up: **8/8**.
- owner exit by SIGKILL and watchdog exit0: **8/8**.
- watchdog authority: `none` in every row.

Death-confirm -> verified-empty:
- pipe-only median **0.998472 ms**, max **2.302456 ms**;
- watchdog-journal median **1.0533325 ms**, max **3.520816 ms**.

Verified physical key-up precedes ordinary data recovery in every row; minimum lead is **155.642939 ms**.

## Audit chronology

The byte-frozen A2 auditor ran only after all eight first rows existed. It raised `KeyError: 'journal_write_done_ns'`: the journal persists the pre-fsync receipt containing `journal_write_start_ns`, while `journal_write_done_ns` is added to the evaluator watchdog receipt after fsync returns. No live row was rerun.

A read-only one-line audit-v2 correction reads the done timestamp from the watchdog receipt while keeping the persisted journal content check unchanged. Audit-v2 returns `PASS_WATCHDOG_RECEIPT_RECOVERY_SCOPED`, errors `[]`. Copied-evidence corruptions reject **4/4**; postformal source rehash is exact and A2 static tests re-pass **3/3**.

## Interpretation

When the ordinary input owner is dead, a surviving cleanup-only watchdog can still release held input independently of a blocked ordinary data plane. If its compact cleanup receipt is only sent once through that blocked pipe, the safety action remains real but the receipt is lost. Persisting the watchdog receipt **after verified key-up** in a local fsynced journal preserves later recovery without moving persistence onto the pre-release critical path.

## Limits

Linux/Xvfb/XTEST/Tk/process-death/filesystem evidence only. Watchdog survival is assumed. Local `fsync` is not power-loss proof. This does not establish X-server-stall tolerance, host crash, physical-device semantics, distributed durability, cross-platform behavior, hard real-time guarantees, or production readiness.
