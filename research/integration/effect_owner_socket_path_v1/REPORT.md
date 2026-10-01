# Effect-owner receipt through live Unix-socket path v1

Decision: **FAIL_SOCKET_RECEIPT_TRANSPORT**.

## Result
The frozen 12-case formal block ran exactly once with zero reruns. The live AF_UNIX/EventCursor path returned the expected scoped `effect_evidence` boundary in **11/12** cases. Exact owner receipts arrived and revalidated **6/6**. Forged-manifest records arrived in **5/6** cases and caller-side durable-owner revalidation accepted **0/6** (correctly zero). Every case retained exactly one authoritative owner effect and every socket response that returned records exposed `authority=none`; overall authority-none is **12/12**.

One preregistered forged/action case (`f3-2-forged_manifest-action`) returned `timeout` with zero records even though the server exited 0 and its SQLite owner retained the one effect. Under the frozen decision rule this is `FAIL_SOCKET_RECEIPT_TRANSPORT`; the allocation is not retried or upgraded from the 11/12 near-pass.

## Interpretation
The provenance discriminator works on every received record: exact receipt 6/6 accepted; forged receipt 0/5 accepted. The failed case is therefore not evidence of a receipt-provenance escape. It exposes a live integration liveness boundary: `event_socket_v11` publishes the socket endpoint before a bounded read has proof that the child producer has emitted the awaited record. A one-second scoped wait can therefore expire before source publication under this container schedule. This concrete readiness gap must be isolated separately before #548 can be called closed at the live-socket level.

## Integrity
- formal rows: 12 first outcomes; formal invocations 1; reruns 0;
- independent SQLite/result audit decision: `FAIL_SOCKET_RECEIPT_TRANSPORT`;
- frozen source rehash: 15/15 exact;
- RESULT SHA-256 `4cbfe62e0337f795c40a591e704fb4dea1c263a76dc2d85e8a21a47cd045866e`;
- AUDIT SHA-256 `0e68ae45972115ee6e29a1493f6254e4f8b0215b0730bf91abaab5b8dff92b76`;
- FREEZE SHA-256 `e8d670080fe2aa4a3712ff34d5b0cfd953223322367655ba6d31c389eb8aea08`;
- SOURCE_BUNDLE SHA-256 `78f066b50ea442a519900d04f7945f65882cf36452e86f206b3ae4ae8e8bd3b7`.

## H/T/D/C/U
**H:** existing scoped `effect_evidence` can carry a durable owner receipt through the live socket, with caller-side owner revalidation detecting nested receipt forgery.

**T:** exact current transport dependencies, fresh owner DB and subprocess/socket per case; 3 reps × 2 receipt modes × 2 scopes.

**D:** frozen PASS required 12/12 outer boundaries plus exact/forged provenance gates. One transport timeout triggers the retained FAIL.

**C:** the timeout is consistent with producer-readiness scheduling rather than JSON field corruption: the server exited cleanly and the authoritative effect existed, while no record crossed the cursor before the wait expired. The frozen allocation does not rerun the case to prove that causal explanation.

**U:** same-user local AF_UNIX and synthetic child only; no authentication, hostile transport, GUI/model/token/latency/product claim. Timing values are descriptive and not used as a performance result.
