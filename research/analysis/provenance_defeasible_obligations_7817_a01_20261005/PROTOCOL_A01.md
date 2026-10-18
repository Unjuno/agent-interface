# A01 protocol and freeze

Allocation: `PROVENANCE-DEFEASIBLE-7817-T0-A01-20261005-01`  
Issue: [#7817](https://github.com/Unjuno/agent-interface/issues/7817)  
Fresh main at freeze: `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`  
Branch: `research/7817-provenance-defeasible-t0-a01-20261005`

## H / T / D / C / U

**H:** For a finite hand-authored policy language, the candidate produces the
expected advisory obligations and source-bound derivations only when explicit
priority provenance is valid, while all ambiguous, incomplete, out-of-scope,
unauthenticated, cyclic, or strict-prohibition conflicts stop without changing
authority.

**T:** Evaluate ten frozen contexts in `fixture.json`: in-scope and out-of-
scope exception, incomparable conflict, invalid edge, priority cycle, strict
prohibition, duplicate source/version identity, conditional specificity,
irrelevant evidence addition, and revocation/supersession. The candidate also
evaluates five frozen hostile mutations (source-span removal, issuer forgery,
scope widening, inserted priority cycle, and defeasible attempt against a
strict prohibition). An independently authored expected-outcome ledger audits
all rows, proof paths, boundary flags, denominators, and mutations. No network,
model, GUI, user data, GPU, shared runtime, or external effect is used.

**D:** `PASS_METHOD_SCOPED` only if the independent audit exactly reconstructs
all ten decisions and derivations, all five mutations stop with their declared
reason and no obligation, no row changes authority, and the two construction
tests pass. Any mismatch is `FAIL_METHOD`; missing evidence or environment
failure before candidate is `STOP_ENVIRONMENT`. No post-freeze repair or retry.

**C:** A precedence-free conflict ledger may be simpler; a decision table may
be more auditable than defeasible inference; authentication and complete source
extraction may dominate evaluator correctness; the fixtures are authored.

**U:** Finite synthetic semantics only. The tests cannot establish policy
legitimacy, source authenticity, correct interpretation, rule completeness,
real GUI behavior, action safety, benefit, or authority. A resolved advisory
obligation is not a permission token.

## Runtime choice and immutable freeze

The issue explicitly defines T0 as a small deterministic finite-state CPU
fixture; a container is not required. The shared WSLc lane has unresolved
cross-task allocation/readiness records, so this strictly local host-CPU test
does not access it. It uses Windows / CPython 3.11.9 and only standard-library
code. Candidate and audit limits: one invocation each; retries: zero.

`FREEZE.json` binds the exact fixture, candidate, independent auditor, tests,
and protocol bytes; commands; environment; main base; and zero formal
invocations at freeze. The formal run may write only the new `raw/` directory.
