# XTerm semantic-receipt transport diagnostic A2

Issue #1595. Execution-packaging-only successor to #1578; all #1578 partial formal rows are pooled0.

## Formal first outcome

All four immutable 5-pair batches completed exactly once. Total:20 matched pairs /40 fresh XTerm sessions. Integrity passes40/40: exact PTY byte, focus readback, press-before-frontier, receipt validation, terminal QueryKeymap x-UP and XTerm/helper exit0.

### Primary comparison

Atomic-file polling:
- drain median5.677822ms;
- drain p95 **5.915045ms**;
- drain max5.943879ms;
- publication/effect-to-parent-seen p95 **0.518721ms**.

AF_UNIX datagram:
- drain median5.479098ms;
- drain p95 **6.142695ms**;
- drain max6.165693ms;
- publication/effect-to-parent-seen p95 **0.369055ms**.

Matched file-minus-dgram total-drain median improvement: **0.214561ms**.

The preregistered localization PASS required:
- dgram transport p95<1ms;
- dgram drain p95<6ms and max<8ms;
- matched median total-drain improvement>=0.75ms.

The carrier itself is fast enough, but total drain p95 remains above6ms and the matched improvement is far below0.75ms.

Disposition: **HOLD_TRANSPORT_NOT_DOMINANT_A2**.

## Posthoc timing decomposition

Descriptive only; not a preregistered decision gate.

Effect-ready after XTEST release:
- file median5.270388ms / p95 5.487070ms / max5.655026ms;
- dgram median5.292382ms / p95 **5.778333ms** / max5.966357ms.

Press→raw-PTY input receive:
- file median0.841519ms / p951.129486ms;
- dgram median0.870616ms / p951.416073ms.

Median transport share of total drain:
- file6.10%;
- dgram2.76%.

Thus the receipt carrier is a minority of the total drain in this fixture. Session-to-session PTY/XTerm/input-receive + semantic-ready timing dominates the tail. The faster dgram carrier cannot compensate for that variation and does not rescue the original A5 speed envelope.

## Integrity

Independent audit: PASS, errors[]; scientific decision remains HOLD.
Corruption controls4/4 rejected: dropped row, duplicate identity, terminal key-down, invalid receipt.
Formal invocation1; batch reruns0; replacements0; tuning0.

## Scope

Private same-host X11/XTerm/local IPC only. No model/provider/network/user desktop/MAP01/shared runtime. This does not overturn #1555 or promote AF_UNIX as a production transport.
