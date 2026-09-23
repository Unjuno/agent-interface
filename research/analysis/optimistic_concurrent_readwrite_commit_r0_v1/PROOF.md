# Pairwise optimistic-commit criterion

Let intent A have complete read set `R_A` and write set `W_A`; intent B has `R_B`,`W_B`. Prepared read versions are bound to the evidence used by each intent. Assume equality of a version token means equality of the evidence relevant to that read, every relevant mutation changes the token, each intent's own final validation+effect is linearized, and overlapping writes have no independent commutativity certificate.

## Sufficiency

If every resource in `R_A ∪ R_B` still has its prepared version and

- `W_A ∩ W_B = ∅`,
- `W_A ∩ R_B = ∅`,
- `W_B ∩ R_A = ∅`,

then neither intent writes a resource read by the other and they do not write the same resource. Thus one intent cannot invalidate the other's complete read-dependent semantics, and their write effects occupy disjoint resources. Under the stated individual-linearization assumption, either execution order has the same pairwise dependency validity, so parallel admission is safe with respect to the pair.

Read/read overlap is harmless because neither participant mutates that shared resource.

## Necessity for universal safety

Each failed condition has a deterministic counterexample.

1. **Stale read:** if `x ∈ (R_A ∪ R_B)` changed after preparation, choose the affected intent's output as `F(x)=x`; its prepared result differs from fresh evaluation.
2. **A-write/B-read:** for `x ∈ W_A ∩ R_B`, let A write `x:=1` and B's result be `F_B(x)=x`. Concurrent ordering can make B's prepared/read-dependent result disagree with the state after A.
3. **B-write/A-read:** symmetric.
4. **Write/write:** for `x ∈ W_A ∩ W_B`, let A write `x:=0` and B write `x:=1`. Final state depends on order, so generic unordered parallel commit is not universally equivalent.

Therefore, absent a stronger commutativity/transaction proof, the three set-disjointness conditions plus exact read currentness are necessary for a universal generic parallel-admission rule.

## Boundary

This theorem says nothing about how complete dependencies are reconstructed. If a relevant read is omitted, the sufficiency premise is false; #501/#508 already retain that boundary. It also does not prohibit an explicitly certified commutative W/W overlap.
