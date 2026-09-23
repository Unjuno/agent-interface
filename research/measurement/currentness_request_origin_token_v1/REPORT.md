# Currentness request-origin token — first outcome

Task: `CURRENTNESS-REQUEST-ORIGIN-TOKEN-20260918-005`  
Issue: #1126  
Frozen branch: `research/currentness-request-origin-token-20260918-005`

## Disposition

**`PASS_CURRENTNESS_REQUEST_ORIGIN_TOKEN_SCOPED`**

This is a scoped synthetic lifecycle/construction result. It is not runtime promotion, real transport/concurrency evidence, model/task benefit, latency/token evidence, or a production ABI claim. Per the frozen stop rule, a later fresh formal allocation is still required before promotion.

## One-factor repair

The predecessor #1118 exposed an in-flight response laundering gap: a request authored from epoch 0 could return after invalidation advanced the runtime to epoch 1, then be stamped at arrival time and admitted. This candidate adds only a runtime-owned request record containing the request's origin epoch. `INSTALL_RESPONSE` consumes the request and installs a decision only when stored origin epoch equals the current runtime epoch. Planner generation remains opaque provenance and never controls currentness.

## Primary result

- primary invocations: 1; reruns: 0
- deterministic seed: `112620260918005`
- transitions: 600,000 across 14,972 random traces
- independent candidate/oracle mismatches: 0
- exact transition digest: `a5f9cfa732dc0b03051eac72c713b192e0d464d9451252ba273b21dfcdedf8b0`
- stale-origin response installs: 0
- stale old-epoch admissions: 0
- response replay installs/rebindings: 0
- duplicate invalidation double-advances: 0
- cross-scope mutations: 0
- authority promotions: 0
- valid fresh installs: 52,127
- valid fresh admissions: 6,345
- planner generations exercised: [0, 1, 2, 100, 1000000, 2147483647]
- malformed fail-closed controls: 10/10
- bounded exhaustive traces: 1,364; mismatches 0; stale installs 0

Status counts include 19,050 explicit stale response refusals and 52,271 consumed-request replay refusals.

## Independent audit / integrity

Independent auditor: **PASS**, errors `[]`. The auditor independently regenerates the fixed random schedule and state history without importing the candidate implementation and reproduces the exact transition digest and aggregate counts.

All seven scientific source files retained the exact SHA-256 values recorded before the primary invocation: source unchanged = `true`.

Result SHA-256: `16d0deb606e54a47583fa74f3593c0bb8b0a6bdfafa06a574994513380c7806b`  
Audit SHA-256: `5a5e2ce2dce52d0d93635fc79e7c1fb6732c064b96f829de18e874d686324703`  
Invocation-sentinel SHA-256: `897ec77e5a2b92e4d8427d1a8bef4803d3d8cdc61689288d2eac9714a4a23fb8`

## Interpretation

Within the frozen synthetic state model, binding a planner response to a runtime-owned request-origin epoch closes the exact stale in-flight laundering class exposed by #1118 while preserving fresh post-invalidation requests. The experiment also supports the intended separation: planner generation does not create currentness, request/response operations grant no input authority, and a consumed request cannot be reused to install a new decision.

## Limits / next discriminator

The result does not exercise real cancellation, concurrent request transport, process crashes, a frontier model, GUI/X11, or real task input. The next valid step is a separately frozen fresh formal allocation or shadow integration that preserves the same request-origin semantics while testing actual concurrent request/invalidation ordering. Do not widen authority or infer task-speed/token benefit from this result.

## Corruption controls

Frozen result mutations rejected by the independent auditor: **8/8** (`digest`, `stale_install`, `stale_admit`, `replay`, `authority`, `decision`, `invocations`, `pgen`). The first synchronous postformal attempt hit the outer tool timeout before producing a control artifact; the exact frozen control script was then executed once via detached transport with unchanged logic. This was not a scientific primary rerun.

CORRUPTION SHA-256: `fb8b9de6364c2e5c65062e936665acad63329045d2a5986f4e67cf57d07a42b9`  
Final integrity source-unchanged: `true`.
