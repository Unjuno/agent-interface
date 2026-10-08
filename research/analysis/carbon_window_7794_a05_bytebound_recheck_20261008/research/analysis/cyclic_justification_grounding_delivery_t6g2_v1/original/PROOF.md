# Conditional proof: rooted support after deletion with positive cycles

## Variables and assumptions
All quantities are dimensionless (SI 1), discrete graph or set quantities, not
time, pixels, probability or physical truth.

|Symbol|Meaning (日本語)|Unit|Definition|Domain/assumption|Type|
|---|---|---|---|---|---|
|B|基礎証拠ノード|1|fixed finite root universe|disjoint from D|set|
|D|導出主張ノード|1|fixed finite derived universe|finite|set|
|V|全ノード|1|B union D|finite|set|
|J(h)|主張hの代替根拠集合|1|finite family of nonempty antecedent sets|each subset of V; h in D|family of sets|
|h|規則の結論|1|head of one justification|h in D|node identifier|
|j|規則の前提集合|1|one member of J(h)|AND within j; OR across J(h)|set|
|E|撤回前に利用可能な基礎証拠|1|active roots before update|E subset B|set|
|E'|撤回後に利用可能な基礎証拠|1|active roots after update|E' subset E|set|
|R|撤回された証拠|1|E setminus E'|subset B|set|
|S_k|根拠からk段で得られるノード|1|closure iteration defined below|k nonnegative integer|set|
|k|反復段数|1|synchronous iteration number|nonnegative integer|integer scalar|
|G(E)|根拠から有限導出できる集合|1|least rule-closed set containing E|roots exactly E|set|
|A|撤回の影響範囲|1|derived nodes reachable from R via support-to-head edges|subset D|set|
|U|影響範囲外|1|D setminus A|subset D|set|
|W_0|局所再導出の初期集合|1|E' union (G(E) intersect U)|subset V|set|
|W|局所再導出の終端集合|1|closure restricted to heads in A from W_0|subset V|set|
|M|規則に対して閉じた解釈|1|contains E; every satisfied rule includes its head|subset V with M intersect B=E|set|

Rules are positive, complete, unchanged and evaluated synchronously on one
stable snapshot. A claim is grounded iff it has a finite proof tree with leaves
in active roots. There are no empty-body facts, negation, defaults, priorities,
probability or autonomous action permissions. Cyclic graphs are allowed.

## 1. Least grounding and the independent oracle
Set S_0=E. For k>=0 define

S_(k+1) = S_k union {h in D : there exists j in J(h) with j subset S_k}.

Every step only adds derived nodes. A changing step adds at least one, so there
are at most |D| changing steps. Let the terminal set be G(E). It contains E and
is closed under every rule, because otherwise another changing step exists.

For any closed interpretation M containing E, S_0 subset M. If S_k subset M,
then every body contained in S_k is contained in M; closure of M requires its
head in M. Hence S_(k+1) subset M. Induction gives G(E) subset M for every M.
Since G(E) is itself one such M, it equals their intersection. This proves
why enumerating all closed interpretations gives an independent exact oracle;
no candidate evaluator is needed by that oracle.

Membership in S_k implies a finite proof tree: roots are leaves; every newly
added head attaches the already-constructed trees for its body's antecedents.
Conversely, induction on the height of any finite proof tree puts its root in
some S_k. Thus least grounding equals finite rooted derivability. A cycle
with no root-derived entry does not become true just by pointing to itself.

## 2. Deletion cannot add grounded claims
G(E) contains E' and is closed under the unchanged rules. By the minimality
proved above, G(E') subset G(E). Equivalently, induction compares the closure
sequences starting from E' and E. Both proofs use E' subset E; insertions and
rule changes are outside this theorem.

## 3. Unaffected grounded claims remain grounded
Create a directed edge from every antecedent to the head of its rule, including
each antecedent of an AND body. A is the derived-node reachability closure from R.
If a head is in U, none of its antecedents can be in R or in A: such an edge
would place the head in A. For a previously grounded head in U, inspect a finite
old proof tree. Its derived antecedents stay in U recursively, and its active
root leaves cannot be in R. Those leaves remain in E'. The same finite tree
therefore proves the head in G(E'). Thus G(E) intersect U subset G(E'). Combined
with Section 2, the old and new grounded sets agree on U.

## 4. Local clearing and rederivation is exact
Begin with W_0=E' union (G(E) intersect U). Section 3 proves W_0 subset G(E').
Repeatedly apply only rules whose heads lie in A, adding a head when all of
its antecedents are already present. Every seed has a finite proof and every
addition preserves finite proof existence. Therefore every intermediate set,
and terminal W, is contained in G(E'). Termination needs at most |A| additions
of distinct heads, hence at most |A| changing synchronous rounds.

To prove completeness, show W is closed under ALL rules. For a head in A,
closure follows from termination. For a head in U with body contained in W,
we have W subset G(E') subset G(E). Hence the body is also in G(E), so old
closure entails that head is in G(E). Because it is in U, it was included in
W_0 and therefore in W. Thus W is closed and contains E'. Least-model minimality
implies G(E') subset W. Combining both inclusions gives W=G(E').

This is conservative syntactic-cone clearing plus rederivation. It is related
to, but not represented as the full DRed implementation or an optimal algorithm.

## 5. Two comparators have different one-sided errors
Local pruning starts with old derived claims plus E' and repeatedly removes
claims with no body satisfied in the current set. G(E') remains a subset at
every step: each grounded claim has a supporting rule in G(E'), and therefore
also in the current superset. Thus this comparator cannot lose genuinely
new-grounded claims under these premises. It can retain too many, because a
supported cyclic set need not be the least grounded model.

Blind cone clearing returns W_0 without rederivation. Section 4 proves
W_0 subset G(E'), so it cannot falsely retain under these premises. It can lose
claims supported by an alternative outside the retracted evidence.

## 6. Concrete counterexamples
One active evidence node 0; derived claims 1 and 2. Rules:
1 <- {0}, 1 <- {2}, 2 <- {1}.
Before withdrawal both claims have finite root proofs. After withdrawing 0,
S_0 is empty and no rule is enabled, so grounded claims are empty. Yet {1,2}
satisfies every local OR-of-AND support check. Local pruning retains both.

Now use roots 0 and 1, claims 2 and 3, and rules:
2 <- {0}, 2 <- {1}, 2 <- {3}, 3 <- {2}.
After withdrawing 0 but retaining 1, both claims lie in the affected cone.
Blind clearing drops both. Rederivation uses 1 to restore 2 and then 3.

An alternative 2 <- {1,3} cannot provide an independent seed if 3 is grounded
only by 2. Every antecedent must have a rooted proof; one live root in an AND
body is not enough.

## 7. Units, scope and failure of assumptions
All operations are union, intersection, difference, reachability and Boolean
membership on subsets of the same V. Counts measure nodes/rules; units are SI1.
No byte, time, probability or physical uncertainty is combined with them.

Missing support remains a decisive limitation: suppose the actual condition
is claim2 <- {root0,root1}, but the declared graph records only {root0}. With
root0 active and root1 withdrawn, the declared least model retains claim2 while
the complete condition does not. The algorithm cannot discover the omitted edge.
Likewise a finite proof proves only the declared logical support, not observation
truth, freshness, authenticity, or that any GUI action is permitted.

## ERROR CHECK
Covered termination, least-model uniqueness, finite derivability, deletion
monotonicity, unaffected-region preservation, soundness and completeness of
restricted rederivation, self/mutual cycles, AND/OR distinction and independent
alternatives. No theorem about negative/default logic, concurrent graphs,
missing evidence truth, temporal authority, performance or product safety.

## Primary reference
Gupta, Mumick & Subrahmanian (1993), Maintaining views incrementally.
DOI:10.1145/170036.170066. Existing recursive view-maintenance background;
this note proves its own narrower finite positive-graph contract from definitions.
