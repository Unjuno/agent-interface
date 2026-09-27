# #1441 T1 integrity successor A7

Fresh successor to retained #1438 `FAIL_INTEGRITY / no rerun`.

Scientific mechanism is unchanged: exact #1378 state->disposition mapping, 5 ms sampling, one F8 on observed CLEAR entry, six frozen scenarios, request0/handback40 ms, process-isolated private X11.

A7 changes evidence integrity only:
1. after local authority is closed at handback, retain any frozen transition with nominal offset <=40 ms that was not yet recorded; this evidence flush cannot emit input;
2. independent audit requires the exact per-scenario transition program in both arms;
3. candidate sends must match observed CLEAR entries exactly;
4. TRANSIENT_8 resume effect must occur before handback;
5. any integrity defect has decision precedence over authority/watch/timing/value.

Pre-lease work is source/static only. No X11 session is authorized by this source freeze. A finite #60 lease is required before the excluded TRANSIENT_28 construction pair or fresh formal block.
