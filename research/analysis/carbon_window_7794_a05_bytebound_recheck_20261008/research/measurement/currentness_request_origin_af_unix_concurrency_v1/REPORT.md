# #1243 concurrent AF_UNIX request-origin transfer — first outcome

Decision: `FAIL_CURRENTNESS_REQUEST_ORIGIN_AF_UNIX_CONCURRENCY`  
Primary invocations: 1; reruns: 0.

## Scientific result
- 20,000/20,000 cases completed.
- Candidate/oracle mismatch: 0.
- Stale response installs: 0.
- Stale old-epoch admissions: 0.
- Race owner-order errors: 0.
- Race order coverage: install-first 1202; invalidation-first 1298.
- Cross-scope mutations: 0.
- Replay rebindings / duplicate double-advances / authority promotions: 0 / 0 / 0.
- Malformed transport controls: 5/5 fail closed.
- Four distinct client PIDs observed.
- Owner receive→apply ns p50/p95/p99/max: 51158/98782/321090/4122105.

## Why the frozen PASS gate failed
The independent audit is `FAIL` only because cleanup was not clean: the AF_UNIX server captured one `ConnectionResetError: [Errno 104] Connection reset by peer` traceback in stderr after the malformed oversize transport control closed its connection. The 20,000 retained scientific cases have family-invariant errors0 and all currentness/race/scope/replay/authority gates above pass, but #1243 preregistered server/client exceptions0 plus cleanup/integrity. Therefore this first outcome must not be upgraded to PASS.

This is a transport-plumbing failure, not evidence of a stale-currentness escape. A legitimate successor must retain this failure, change only peer-reset handling at the AF_UNIX boundary, use a fresh task/seed, and rerun as a new allocation.

## Integrity
- Ledger: 20,000 JSONL rows; SHA-256 `14318b345b35ae84e3e5203ff989ca81fa2f2e576cc747222f35384b3b68a438`.
- Formal result SHA-256 `44e2679f4c4d7fdb661574727b957ad4fc55d234d3833fdac951a020e97bc290`.
- Audit SHA-256 `8d684902b2430a537e8d3662616ed815ca95b596ee5661384c5c57ba990349ff`.
- Corruption controls: 9/9.
- Frozen A2 source unchanged: true.
