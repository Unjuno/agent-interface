# Ordered interrupt batching — #1871

Task: `EVENT-ORDERED-INTERRUPT-BATCHING-20260919-001`

H: after classification/coalescing/budget/arbitration are fixed, batching is semantics-preserving only when it treats scheduler output as an immutable ordered sequence. Re-prioritizing members inside a batch can reverse causal event order.

T: stdlib-only deterministic container. Batch size 4. Directed causal/critical/terminal controls plus exhaustive sequences length 0..6 over four event classes × two sessions. Candidate flattened output and every prefix must equal input exactly. Independent audit reimplements batching and corpus enumeration.

D: PASS iff sequence/identity/per-session projection/metadata exact, naive priority-sorted comparator exposes at least one directed reversal, delivery reduction exists, malformed controls reject, and formal1/reruns0/replacements0/tuning0.

C: representation-only after scheduler decisions. No claim about model comprehension, tokens, transport atomicity, wall time, natural event rates, ACK/resolution, or production batch size.

U: deterministic finite corpus only; no GUI/model/network/input/runtime mutation.
