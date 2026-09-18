# CURRENTNESS-REQUEST-ORIGIN-AFUNIX-SHADOW-20260918-007

BASE: bddb2ede50dedc36aae0571c0310c45625042796
PARENTS: #1126 / #1234
EXACT CANDIDATE GIT BLOB: 3e9fc5474de9af820b653c36e5db5d912edfc076

H: hold the request-origin barrier and add only actual AF_UNIX subprocess response transport plus independent invalidator thread ordering.
T: 4 frozen strata x128 =512 cases, persistent planner subprocess over socketpair, newline JSON, ACK/release happens-before barriers, fresh barrier per case, all planner-generation magnitudes, independent timeline/status audit, source-first primary1/reruns0.
D: PASS_REQUEST_ORIGIN_AFUNIX_SHADOW_SCOPED iff512/512 complete, parse/errors/residual0, stale-inflight refused128/128, fresh-after-invalidation admit128/128, response-before-invalidation later-use stale128/128, transport replay refused128/128 with rebind0, timeline violations0, oracle mismatch0, authority promotions0, planner-generation influence0, integrity/audit pass.
C/U: causal barriers test composition not race probability/throughput; Linux container only, no remote planner/process crash/task/model/GUI/production claim.
