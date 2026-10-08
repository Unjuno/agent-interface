# A02 formal first outcome

- Candidate: one invocation, exit 0; 177 rows (`candidate_rows=177`).
- Independent auditor: one invocation, exit 0; disposition `PASS_METHOD_SCOPED`, 177 rows checked, zero errors.
- All 52 set partitions of five A requests were present. The one-identity presented-debt baseline allocates 2 service units each to A and B.
- Caller-presented debt gave A more than 2 units in 46/51 nontrivial partitions: 39 partitions allocated A 3 units, and 7 allocated A all 4 horizon units. Five partitions were nulls and remain in the result.
- Trusted-parent service-debt order matched the one-identity trace in 52/52 partitions. FIFO request order was `A0,B0,A1,B1` in 52/52 partitions.
- Construction tests rejected 5/5 frozen corruption controls before the formal freeze. No formal rerun or retry.
