# Pre-freeze construction history — excluded from T0 result

These finite outputs were produced before the source freeze to check fixture
shape and inspect the enumerated equality terms. They are preserved for
transparency but are **not** the formal candidate/auditor result, were not
preregistered evidence, and must not be used to claim `PASS_METHOD_SCOPED`.
The formal pair will use a distinct `formal_01/` output path after the
preregistration comment and source commit.

1. Initial CLI smoke, before independent closure audit was added:
   `python3 candidate.py --out /tmp/issue7462-construction/raw.json`; exit 0,
   three program rows. Preserved as
   `construction_pre_freeze/initial_cli_smoke.raw.json`, SHA-256
   `4c79ddee64409a8b3d2a0025125cfe80a1442bee622040a6bd46b23ac46df490`;
   candidate source SHA in that output:
   `c4717184cb27251e8ced7797311b5858cd013ff53d45864725ae9ccee519f24e`.
   The candidate and auditor were strengthened afterward; this raw is stale
   construction only and excluded from formal counts.
2. After the independent closure-check changes, a construction-only in-memory
   `candidate.run(fixture)` wrote `/tmp/issue7462-construction/source-review.json`;
   three program rows, SHA-256
   `d77b5d71f91ecd3511ade9099490da297f6a8cabaad044bd068fd5d92cd61a2e`;
   candidate source SHA:
   `f0d912ecfd38c4945db5add5dba5f4c5f5a3a7b2eacca5f654a8337477ef6d67`. This
   was still pre-freeze and had no independent formal audit.
3. Package construction tests passed 3/3 and `py_compile` passed. The earlier
   raw CLI smoke and the in-memory review are retained separately; neither is
   reused as the one post-freeze candidate invocation.

The test protocol, fixture, candidate, auditor, and test source will be
committed/frozen after this construction stage. Any formal result remains
separate and one-shot.
