# Successor #2144: barrier recovery pre-model policy boundary

## H/T/D/C/U

- **H**: A generation/content-bound recovery policy distinguishes visible ACK, lost ACK, non-commit, changed read, unavailable read, and duplicate/replay ambiguity without advancing authority from timing or mode equality.
- **T**: Six frozen cases compare typed evidence against `ADVANCE`, `READ_BACK`, `RETRY_IDEMPOTENTLY`, `HOLD`, and `ABORT` decisions.
- **D**: Standard-library deterministic policy/oracle; no network, model, GUI, runtime, task input, or real transport.
- **C**: Exact expected generation/content is required for advance; ambiguous ACKs read back; retry is reserved for non-commit with generation-bound idempotence; changed/unavailable evidence cannot advance.
- **U**: Model recovery choices, real transport failures, restart/fanout behavior, latency, cost, and production exactly-once semantics remain unmeasured.

## Disposition

`HOLD_PRE_MODEL_BARRIER_RECOVERY_POLICY`: 6/6 oracle agreement, blind retries 0, stale advances 0, duplicate writes 0, authority grants 0, model invocations 0. This is a policy boundary, not a real transport or model result.
