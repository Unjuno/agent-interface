# Service Manifest discovery closure R1

Task SERVICE-MANIFEST-DISCOVERY-CLOSURE-R1-20260918-001 / Issue #1623.

H: one transport-neutral stable manifest can answer twelve parent #1597 discovery queries without embedding dynamic session capability state. Required omissions/corruptions must fail closed; additive unknown fields remain forward-compatible; incompatible major versions reject.

T: independent resolver + requirement oracle; directed controls; 180,000 generated manifests, including exactly 120,000 single-required-field omissions (10,000/query), plus valid/multi-omission/wrong-type/incompatible-major/forbidden-session/additive-extension families. Canonical JSON must ignore key order.

D: PASS iff candidate/oracle mismatch0, all valid/additive cases pass, omissions/corruptions invent nothing, incompatible-major/session-inline accepts0, canonical reordered digests equal, every required query has >=10,000 failing mutations, formal1/reruns0, audit/corruption/source integrity pass.

C: this validates one reference shape, not globally minimal field grouping or final ABI/wire format.

U: no transport/usability/token/security/latency claim.
