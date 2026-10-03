# Visibility is an information boundary

Let S be a finite concrete state set, p:S->V the projection onto the declared
visible semantic predicates, and o:S->{FAIL,PASS} the independently required
oracle. We ask whether some deterministic f:V->{FAIL,PASS} satisfies
f(p(s))=o(s) for every s in S. This is expressibility, not learning speed.

**Criterion.** Such an f exists iff o is constant on every fiber of p.

Necessity: if p(s)=p(t), a deterministic function receives the same argument,
so f(p(s))=f(p(t)); agreement with the oracle then requires o(s)=o(t).
Opposite labels in one fiber are an impossibility witness, independent of
the number of refinements, fit attempts, or repeated counterexamples.

Sufficiency: for each observed v, choose any s with p(s)=v and set f(v)=o(s).
Constancy makes this choice well-defined. Values outside p(S) are irrelevant
to this finite statement. A complete truth table is a constructive witness;
we do not claim an efficient formula, learned generalization, or that S
enumerates a real application's states.

Here S={false,true}^5 and o(s)=PASS iff all five coordinates are true. The
restricted projection forgets reversibility. Its 16 fibers each contain two
states. Fifteen fibers have at least one visible false coordinate and hence
two FAIL labels. The remaining fiber has all four visible coordinates true:

| Concrete state | Visible evidence | Required label |
| --- | --- | --- |
| case_030: true,true,true,true,false | true,true,true,true | FAIL |
| case_031: true,true,true,true,true | true,true,true,true | PASS |

Thus no total correct Boolean decision rule exists over the restricted
vocabulary. Diagnosis must retain the conflicting pair and declare
ONTOLOGY_INSUFFICIENT; claiming convergence would be false. A fail-closed
partial rule can abstain on this fiber and correctly reject the other 15,
but it cannot both accept case_031 and reject case_030 from this evidence.
Null decisions in the artifact denotes absence of a total correct table,
not an implemented runtime policy or a claim that all fibers are mixed.

The complete projection is the identity, with 32 singleton fibers. The
predeclared table is feasible: one PASS and 31 FAIL. The added coordinate is
not automatically discovered, semantically verified, or authorized by the
checker. Real IR extension still requires reviewed semantics and authority.

Renaming bookkeeping IDs leaves p and o unchanged. Using an ID in f changes
the allowed vocabulary, so it is an invalid solution to the restricted
problem. Repeating a labeled state, even with another bookkeeping ID, leaves
its visible fiber and labels unchanged and cannot resolve the conflict.

This is a small explicit instance of the alias obstruction already observed
in #4294 and #5504; it is not a newly discovered hidden-family false admission.
Its contribution is a reusable pre-refinement expressibility criterion and
a stop/control artifact intended for independent audit for #5504's unexecuted method
follow-up. No comparison against a fake inefficient learner is made.

## Residual obligations

The proof is conditional on correct oracle labels, stable projection semantics,
complete finite enumeration, deterministic total binary decisions, and the
declared vocabulary. Production Verification IR may already expose this
coordinate; no production defect is diagnosed here. Real-app truth, hidden
authority/effect changes, OS races, asynchronous timing, performance, memory
relief, automatic ontology invention and safety remain untested. Old T0/T1/T2
and #4294 results are prior art, not re-executed or rewritten evidence.
