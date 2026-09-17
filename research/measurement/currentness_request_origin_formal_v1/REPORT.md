# Request-origin currentness barrier — fresh formal result

Task: `CURRENTNESS-REQUEST-ORIGIN-FORMAL-20260918-006`  
Issue: #1234  
Parent: #1126 / PR #1231  
Candidate Git blob: `3e9fc5474de9af820b653c36e5db5d912edfc076`

## Disposition

**`PASS_CURRENTNESS_REQUEST_ORIGIN_FORMAL_SCOPED`**

The exact #1126 candidate was held byte-for-byte. Only the formal corpus/seed was fresh.

## Formal evidence

- primary invocation: 1; reruns: 0
- seed: `112620260918106`
- 600,000 transitions across 19,512 traces
- explicit stale-inflight stress: 5,000/5,000 refused; wrong 0
- candidate/oracle mismatch: 0
- stale-origin response installs: 0
- stale old-epoch admissions: 0
- response replay rebindings: 0
- duplicate invalidation double-advances: 0
- cross-scope mutations: 0
- authority promotions: 0
- planner-generation influence: 0
- fresh installs/admissions: 50,643/6,183
- malformed fail-closed controls: 10/10
- exact transition digest: `c6d8856d4071101182a82cd99d837555a20528abd67974d76e51f4d89a69dc21`

The corpus contains 23,448 total stale-response refusals and 51,289 consumed-response replay refusals.

## Audit / integrity

Independent auditor: **PASS**, errors `[]`. It reconstructs the complete fresh schedule without importing the candidate and reproduces the exact digest/counts. Copied-result corruption controls rejected 8/8 mutations. All seven frozen source files are unchanged before/after primary: `true`.

Result SHA-256: `4d5878c9b09aa566fa2d13a20addabf37b0df8186db6ca026e1179148a750a7d`  
Audit SHA-256: `65c44805ec9138410caf2f9732b335b65d1132ab73de6761f4270342234bd931`  
Corruption SHA-256: `4c76eee7a63d2c7b8b091ab09d7119da3a46f48c48f4ef8e37eb1f1ae8346530`  
Invocation SHA-256: `05d50d27b0bff782fb179dd520c2bdcda89df0d821847505b0f0a883e60a878d`

## Interpretation and boundary

This fresh formal supports the scoped request-origin rule: currentness must be bound to the runtime-owned epoch at planner-request origin, not inferred from response arrival or planner generation. The exact #1118 stale-inflight class is rejected while fresh post-invalidation requests still install and admit.

This does **not** establish real IPC cancellation, simultaneous-thread serialization, process failure recovery, frontier-model/task benefit, latency/token gain, GUI/X11/MAP01 behavior, or production ABI. The next rung should be a shadow concurrent-transport integration that preserves this exact contract and adds only actual ordering/concurrency.
