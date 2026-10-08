# Register automaton dynamic identity R0 — proof

## Variables

| symbol | meaning | SI unit | definition | domain / assumptions | type |
|---|---|---|---|---|---|
| `G` | interface-generation identifier set | dimensionless | finite set of generation IDs | nonempty finite set | finite set |
| `T` | target-identifier set | dimensionless | finite set of target IDs | nonempty finite set | finite set |
| `g,g'` | bound/current generation IDs | dimensionless | elements of `G` | `g,g' in G` | discrete scalar |
| `t,t'` | bound/current target IDs | dimensionless | elements of `T` | `t,t' in T` | discrete scalar |
| `m` | generation-domain cardinality | dimensionless | `m = |G|` | integer, `m >= 1` | integer scalar |
| `n` | target-domain cardinality | dimensionless | `n = |T|` | integer, `n >= 1` | integer scalar |
| `r_G` | retained generation register | dimensionless | last value stored by `BIND` | `r_G in G` when bound | register/discrete scalar |
| `r_T` | retained target register | dimensionless | last value stored by `BIND` | `r_T in T` when bound | register/discrete scalar |

All quantities are identifiers or cardinalities and therefore dimensionless. There is no physical-unit conversion in this analysis.

## Frozen behavior

The interface has an unbound state and bound states. `BIND(g,t)` records a generation/target pair. A later `USE(g',t')` is accepted exactly when both identities still match the recorded pair. `RESET` returns to unbound.

The exact acceptance predicate is:

`ACCEPT <=> (g' = g) AND (t' = t)`.

## Proposition 1 — literal no-register lower bound

For finite nonempty `G,T`, any deterministic literal finite-state machine that implements the frozen behavior exactly requires at least `m*n + 1` distinguishable states.

### Proof

1. For every pair `p=(g,t)` in `G x T`, consider the prefix `BIND(g,t)`.
2. Take two distinct pairs `p=(g,t)` and `q=(h,u)`. Since `p != q`, at least one identity component differs.
3. Append the suffix `USE(g,t)`.
4. Starting after prefix `BIND(g,t)`, the suffix is accepted by definition.
5. Starting after prefix `BIND(h,u)`, the same suffix is rejected because `(h,u) != (g,t)`.
6. Therefore the residual behaviors after `BIND(g,t)` and `BIND(h,u)` are distinguishable.
7. Hence all `m*n` bound prefixes occupy different Myhill-Nerode equivalence classes.
8. The initial/unbound prefix is also distinguishable from every bound prefix: for any `(g,t)`, suffix `USE(g,t)` is rejected from unbound but accepted from the corresponding bound prefix.
9. Thus there are at least `m*n + 1` distinguishable residual classes.
10. A concrete machine with one `UNBOUND` state and one literal state for every `(g,t)` realizes exactly `m*n + 1` states.

Therefore the lower bound is tight. QED.

## Proposition 2 — two typed registers are sufficient

A register automaton with two control states and two typed registers implements the frozen behavior exactly for arbitrary identifier values.

### Construction

- control state `UNBOUND` has no valid retained pair;
- on `BIND(g,t)`, store `r_G := g`, `r_T := t`, then enter `BOUND`;
- in `BOUND`, `USE(g',t')` accepts iff `g'=r_G` and `t'=r_T`;
- `RESET` clears the binding and returns to `UNBOUND`.

### Proof by induction on trace length

Base case: before any input, both the frozen oracle and construction are unbound.

Inductive step: assume the construction and oracle encode the same binding status and retained pair before the next event.

- On `BIND(g,t)`, both replace any prior binding with exactly `(g,t)`.
- On `RESET`, both become unbound.
- On `USE(g',t')`, neither changes the stored binding. Both accept exactly when the queried pair equals the retained pair in both components.

Thus state meaning and every `USE` decision agree after every finite trace. QED.

## Proposition 3 — independent renaming equivariance

Let `pi_G` be any bijection on `G` and `pi_T` any bijection on `T`. Equality is preserved by bijections:

`g'=g <=> pi_G(g')=pi_G(g)` and `t'=t <=> pi_T(t')=pi_T(t)`.

Applying both renamings therefore preserves the conjunction defining `ACCEPT`. The register construction depends on relations between values, not their literal names. QED.

## Proposition 4 — one retained identity is insufficient

Assume `m>=2` and `n>=2`.

- Generation-only: choose one generation `g` and two targets `t != u`. After binding `(g,t)`, query `(g,u)`. Generation-only accepts, but the exact oracle rejects.
- Target-only: choose two generations `g != h` and one target `t`. After binding `(g,t)`, query `(h,t)`. Target-only accepts, but the exact oracle rejects. This is the minimal ID-reuse-across-generation witness.
- Control-only accept: any mismatching query after a binding is accepted although the oracle rejects.

Therefore neither one-dimensional projection nor a control-only `BOUND` state preserves exact behavior. QED.

## Dimensional / unit check

The predicate compares identifiers for equality and counts finite states. Every variable is dimensionless; `m*n+1` is dimensionless and has the type integer count. No term mixes incompatible physical units.

## Interpretation boundary

The result establishes symbolic-control structure, not total memory compression. A register still has to store enough information to distinguish current dynamic values. The benefit is that the control graph is domain-parametric instead of containing a literal state for every possible generation/target pair.
