# Conditional budget argument

## Variables

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| B | 総量上限 | 1 (byte count) | 16384 in this study | positive integer | scalar integer |
| C | 注意喚起用上限 | 1 (byte count) | 8192 | 0 <= C <= B | scalar integer |
| n_i | 要求iの本文長 | 1 (byte count) | 4096 here | verified exact positive length | scalar integer |
| L | 消費枠を保持する要求集合 | 1 | charged request identities | single sender owner; identities not reused | finite set |
| D | 本文の完全受信が成立した要求集合 | 1 | receiver BODY journal | at most once per identity | finite set |
| X | 終端キャンセル済み要求集合 | 1 | receiver CANCELED identities | monotone within one receiver epoch | finite set |
| S | 台帳消費量 | 1 (byte count) | sum of n_i over L | admission checks against B and C | scalar integer |

Bytes are counts, not a separate SI base unit. All sums and inequalities combine byte counts only. Diagnostic nanosecond timestamps are not mixed with byte budgets.

## Proof

Initially L,D,X are empty, hence D is a subset of L and S=0.

Admission adds a fresh identity i to L before any body can be sent, only when the resulting S does not exceed B and the CUE subtotal does not exceed C. Staging or delaying a body does not change D. A header acceptance and complete valid body can add i to D only while i is absent from X. The protocol serializes this event with SEAL.

If SEAL is processed after body acceptance, its response is RECEIVED; the sender keeps i in L. If SEAL is processed before body acceptance, it adds i to X and responds CANCELED; all later headers for i are refused before the body. Only a matching CANCELED response lets the sender remove i from L. Such i is not in D and cannot enter D later within the same epoch. A missing or mismatched response does not remove i from L. Reconciliation of an already refunded entry is ignored, preventing a second refund. No identity reuse or mutating retry occurs.

Therefore every possible step preserves D subset L. The total receiver BODY bytes, sum(n_i for i in D), cannot exceed S, which never exceeds B. The same subset argument restricted to CUE identities bounds their total by C. This proves only the defined cooperative, single-epoch, header-before-body protocol, not an arbitrary transport or model endpoint.

## Transient-query counterexample

Let c1,c2 each cost4096 and be staged but not received. They occupy8192 CUE bytes. QUERY returns ABSENT for both. If the sender removes both charges, it admits c3 and two AUTO bodies:12288 bytes. Delayed c1,c2 may still be accepted afterward, giving20480 total and12288 CUE bytes. A correct query was not a terminal exclusion certificate.

HOLD instead refuses c3 and ultimately accepts16384 total when c1,c2 arrive. SEAL cancels c1,c2 before their body transfer and admits c3 plus AUTO, receiving12288 bytes. This is cancellation plus reuse of capacity, not recovery of the original evidence.

## Breaking premises

Losing tombstones on receiver restart, concurrent budget owners without serialization, accepting a body before its header check, falsely authenticated receipt identities, duplicate body acceptance, or unspecified partial-body accounting breaks this proof. Sealing after complete network receipt but before semantic presentation only bounds presentation, not received wire bodies. The experiment explicitly retains these boundaries.

ERROR CHECK: invariant established at initialization and preserved for admission, staging, body acceptance, successful/failed/lost seal and repeated reconciliation. Normal receipt never refunds. Byte units consistent. No lifetime guarantee beyond the declared receiver epoch.
