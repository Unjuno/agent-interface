# Result — FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED

The current-main direct retained-input analyzer reported `measurement_ready=true` for both malformed sequences:

- `ack_before_admission`: admitted=110 ns, input ACK=100 ns, release start=410 ns, release return=420 ns.
- `release_return_before_start`: admitted=100 ns, input ACK=110 ns, release start=420 ns, release return=410 ns.

Both positive controls (ordinary order and all-equal boundary) also reported ready. The auditor reconciled all four raw rows and interval calculations, found no raw/source/arithmetic integrity errors, and rejected 4/4 predeclared mutations. Formal candidate and auditor each ran exactly once, exit 0; retry=0.

This is a finite construction finding only. It demonstrates that the frozen offline analyzer's `measurement_ready` flag does not enforce the two tested adjacent timestamp-order relations. It does not show malformed timestamps in a live run, does not falsify prior raw evidence, and does not establish physical key-up, application delivery, MAP01 control, safety, latency, or task effect. The two previously reported timestamp-inversion examples were not rerun.
