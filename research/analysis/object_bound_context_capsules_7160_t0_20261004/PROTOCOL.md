# Frozen H / T / D / C / U

**H:** Identity-bound context retrieval returns a capsule for the same
object/generation across appearance or location changes while refusing
lookalike, duplicate-label, recycled-generation, and identity-unavailable
cases. Retrieved capsules are descriptive context, never input authority;
changed mutable fields require refresh.

**T:** Enumerate six frozen object-reencounter cases against
SIMILARITY_ONLY, IDENTITY_BOUND, and NO_MEMORY policies (18 rows). Independently
reconstruct decisions, stale-field invalidations, and no-authority outputs.
Corruptions: ignore generation, accept a lookalike, trust unavailable
identity, and grant input authority.

**D:** PASS_METHOD_SCOPED only if the independent oracle matches all rows,
identity-bound retrieval accepts both same-object controls, refuses all four
wrong/recycled/unknown identity controls, marks changed fields stale, returns
no input authority, and rejects all four mutations.

**C:** TargetHandle-style identity revalidation or ordinary re-grounding may
provide the same benefit without persistent capsules; similarity-only recall
may be adequate when identities are unavailable only if it abstains.

**U:** The fixture stipulates object IDs/generations. It does not measure visual
re-identification accuracy, hidden application state, model boundaries,
task correctness, latency, or GUI safety. Identity is not proven by matching
pixels/labels; the capsule itself grants no authority.

Host-only Python standard library; no container-specific semantics. Formal
candidate and auditor each run once after issue preregistration; no retries.
