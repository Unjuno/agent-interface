# #1675 Exact dependency-version criterion for safe compute reuse

Decision: **PASS_EXACT_DEPENDENCY_VERSION_REUSE_SCOPED**

Formal analytical invocation: **1**. Reruns/replacements/tuning: **0/0/0**.

## Theorem

For a deterministic pure job whose declared dependency set is complete, and where each dependency has a non-reused semantic version identity:

1. exact equality of the dependency-version vector is sufficient for semantic reuse;
2. for universal safety across arbitrary deterministic jobs, it is necessary;
3. if a causal dependency is omitted, equality of all declared versions is insufficient.

The statement is deliberately conditional. Version equality is not authority when semantic tokens can be reused, dependencies are incomplete, the job reads time/external state, or execution has side effects.

## Exhaustive finite confirmation

The formal model uses four Boolean evidence items.

- evidence states: **16**
- declared dependency subsets: **16**
- source/current pairs per subset: **256**
- total cases: **4,096**
- exact declared-projection pairs: **1,296**
- mismatched declared-projection pairs: **2,800**
- mismatch discriminator failures: **0**
- hidden-dependency controls: **32**
- hidden-dependency failures: **0**
- empty-dependency projection-equal pairs: **256**

For every declared mismatch, choose any changed declared bit `i` and define the valid deterministic job `F(x)=x_i`. Source and current outputs differ, so a generic reuse rule cannot safely accept that mismatched vector for all possible jobs.

For every omitted dependency `h`, choose source all-zero and current state differing only at `h`. All declared versions match while the true job `F(x)=x_h` changes. Thus completeness is a necessary assumption.

For an empty complete dependency set, a deterministic pure job has no varying evidence input and is constant over this model; the 256 source/current pairs are therefore reuse-safe only under that assumption.

## Integrity

- source-first freeze occurred before the only formal invocation;
- preformal local/remote comment-only source mismatch was detected while formal=0 and synchronized to exact remote bytes;
- postformal Git blob IDs for PLAN/prove/audit are unchanged from the freeze;
- independent audit: **PASS**, all checks true;
- corruption controls: **5/5**;
- exact RESULT SHA-256: `150cfce0c0d52125a1051cbcfd111b761cc926886a60658e2a159b1860a0d7a7`;
- exact AUDIT SHA-256: `6ece3fd756becd90d30fc114e049268f83b9bbf213a906323457daf541e036a6`.

Exact formal outputs are retained as deterministic gzip+base64 files with hashes in `EVIDENCE_MANIFEST.json`; `RECONSTRUCT.py` restores and checks them.

## Consequence for #1663

A scheduler can use exact dependency-version identity as a **semantic reuse gate** only for jobs that explicitly satisfy the theorem assumptions. A mismatch proves only that generic reuse is unsafe; it does not decide whether the correct action is RUN, WAIT, CANCEL or REBUILD. Those are scheduling/policy questions and remain empirical/optimization work.

## Limits

No claim about CPU savings, latency, background-job hit rate, scheduling optimality, model quality, runtime ABI, or product performance. Real systems must separately defend against ABA/version reuse, incomplete declarations, scope mistakes, nondeterminism, clocks/external state, and side effects.
