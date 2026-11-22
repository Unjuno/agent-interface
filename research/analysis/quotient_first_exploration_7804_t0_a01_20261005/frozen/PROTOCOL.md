# Issue #7804 T0 A01 protocol

## H / T / D / C / U

**H.** On the exact finite #6251 transition model, canonicalizing the same-role verifier swap at discovery/enqueue time strictly reduces expanded states and generated transitions versus full named BFS, while preserving all reachable safety predicate labels and providing independently replayable named traces for every unsafe quotient class. Identity-breaking controls fall back to named exploration.

**T.** Fresh allocation APPLICATION-QUOTIENT-FIRST-7804-T0-A01-20261005-01 on current main. Preserve the #6251/#6257 package unchanged. Run four arms over the same frozen model: FULL_NAMED_BFS, POSTHOC_GROUPING, QUOTIENT_FIRST_BFS, and deliberate NAIVE_ALL_ID_QUOTIENT. Validate transition equivariance and predicate invariance for every full state and permitted typed permutation. For each quotient node and each outgoing edge, retain enough raw evidence to independently audit the successor and canonical mapping. Lift one shortest quotient path to every unsafe quotient class through the changing inverse permutation map, then replay each named action/next-state edge against the full named transition relation. Identity breakers are verifier-specific ownership, lease-holder identity, actor-named property, and omitted effect target.

**Runtime.** The Issue's prior T requested WSLc. The user-confirmed macOS direction in docs/CURRENT_GOAL.md selects OrbStack Docker for eligible isolated container experiments. This is deterministic stdlib-only CPU work: pinned cached Python image, network none, read-only source/root, distinct output, one CPU requested and bounded tmpfs. Do not infer CPU enforcement. No existing or shared container is used.

**D.** PASS_METHOD_AND_SEARCH_SCOPED only if all full/quotient safety predicate labels agree; all quotient nodes/edges and symmetry checks audit; every unsafe quotient class has a lifted named trace independently replayed; every identity-breaking control falls back to full named exploration; and quotient-first strictly reduces both expanded states and generated transitions. FAIL_METHOD on any lost/invented safety predicate, invalid edge/lift, unsafe reduction, or no strict reduction. HOLD/STOP before formal calls if current-main/source/raw custody, isolated runtime, or independent audit cannot be established. One candidate call and, only after exit 0, one auditor call; retries zero.

**C.** Full enumeration may be cheaper at this scale once canonicalization and witness bookkeeping are counted. Some identity state may be missing from this finite model.

**U.** Finite authored transition model only. Counts do not establish wall-clock or production memory savings, live-worker interchangeability, fairness/liveness, real effects, runtime authority, GUI behavior, or safety in deployed systems. Candidate and auditor are separate implementations by one author, not independent human review.

## Predecessor custody note

The merged #6257 package's source hashes match its frozen manifest. Its old SHA256SUMS values for candidate.raw.json and audit.raw.json do not match the tracked bytes; the exact tracked blobs are nevertheless identified by the #6257 merge commit and current-main Git blob IDs, and actual byte hashes are recorded in this allocation. The old manifest and outputs are preserved unchanged. This discrepancy is an explicit limitation, not silently repaired.
