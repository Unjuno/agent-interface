# #1250 AF_UNIX peer-reset A2 — first outcome

Decision: `PASS_CURRENTNESS_REQUEST_ORIGIN_AF_UNIX_PEERRESET_A2_SCOPED`  
Primary invocations: 1; reruns: 0.

## One-factor repair
Parent #1243 failed only because a refused oversize malformed peer closed and the server handler let `ConnectionResetError` escape to socketserver stderr. #1250 changes only `runtime_server.py:Handler.handle`: `rfile.readline` is wrapped with `except ConnectionResetError: return`. Candidate semantics, owner queue, protocol, oracle, eight scientific families, case counts and malformed controls are held fixed; formal uses fresh seed 124320260918008.

## Formal result
- 20,000/20,000 cases completed.
- Cleanup: server stderr exactly empty; client errors0.
- Candidate/oracle mismatch: 0.
- Stale response installs: 0.
- Stale old-epoch admissions: 0.
- Race owner-order errors: 0.
- Race order coverage: install-first 1206; invalidation-first 1294.
- Cross-scope mutations: 0.
- Replay rebindings / duplicate double-advances / authority promotions: 0 / 0 / 0.
- Malformed transport controls: 5/5 fail closed.
- Four distinct AF_UNIX client PIDs observed.
- Owner receive→apply ns p50/p95/p99/max: 53100/97906/245603/6540095.

## Interpretation
Within this single-host Python AF_UNIX harness with one runtime-owned serialized owner, the request-origin currentness rule transfers across four concurrent client processes and true install-vs-invalidate races when actual owner sequence is the adjudication source. The one-factor peer-reset termination repair removes the #1243 cleanup-only failure without changing the scientific currentness outcomes. This does not establish remote transport, process-crash recovery, direct concurrent candidate mutation, production ABI, GUI/task benefit, model value, or general latency.

## Integrity
- Ledger SHA-256 `53eb15adb992fc834815af55a338d1aaf626c1bb7d98b3c68737bc162b1f59d8`.
- Formal result SHA-256 `d1f23be82bfdc6b643b7aa1f7fe16092c897e0a40ccb73bace6814fcc63a7535`.
- Audit SHA-256 `1110ee565be988707d73e39811aa396c78fab8dcd8c2ccae5daae2f9449b2661`.
- Corruption controls: 9/9.
- Frozen source unchanged: true.
