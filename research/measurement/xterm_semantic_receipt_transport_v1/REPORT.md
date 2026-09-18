# XTerm semantic-receipt transport diagnostic v1

Issue #1578. Fresh diagnostic after #1555; A5 remains consumed and pooled0.

## Analytical reduction

At semantic delay13ms with an 8ms key hold, the limiting idealized case leaves roughly5ms between release and semantic effect, so the original p95<6ms gate leaves about1ms for publication/transport/wake overhead. This diagnostic compares atomic-file polling with prebound AF_UNIX datagram transport without changing the semantic delay or A5 speed thresholds.

## Construction

Two matched pairs / four fresh XTerm sessions completed with exact input, focus, pre-frontier press, receipt lineage/authority, terminal QueryKeymap x-UP and exit0.

Construction descriptive values:
- atomic-file transport-seen p95 0.431770ms; drain p95 5.682662ms;
- AF_UNIX transport-seen p95 0.174561ms; drain p95 5.493162ms;
- matched file-minus-dgram total-drain median 0.0956045ms.

These four rows are excluded from formal and do not decide the hypothesis.

## Formal execution stop

The single 20-pair /40-session formal invocation exceeded the outer 45s execution envelope before `FORMAL.json` serialization.

At stop:
- session directories38/40;
- complete row files37;
- one incomplete directory `p018-dgram`;
- complete rows: file19, dgram18;
- integrity checks37/37;
- no Xvfb/XTerm/helper residual process;
- aggregate absent.

Disposition: `STOPPED_OUTER_EXECUTION_TIMEOUT_NO_RESULT`.
Scientific disposition: `NONE`.
Formal invocation1; reruns0; poolable formal rows0.

A legal successor may change only execution packaging to immutable batches. It must preserve the frozen transport factor, delay13ms, hold8ms, offset38/frontier40, receipt schema, thresholds and integrity gates. No #1578 partial formal row may be pooled.

## Scope

Private same-host X11/XTerm/local IPC only. No model/provider/network/user desktop/MAP01/shared runtime or production claim.
