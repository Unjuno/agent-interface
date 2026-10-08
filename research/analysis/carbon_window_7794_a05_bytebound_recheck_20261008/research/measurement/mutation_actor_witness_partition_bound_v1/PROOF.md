# Trusted-witness partition lower-bound proof

## Definitions

Let `A` be the finite hidden actor set. A trusted witness maps every hidden actor history to one verifier-visible witness value. Histories with the same witness value form one witness equivalence cell. A requested actor taxonomy is another partition of `A`; every actor in a taxonomy cell is intended to receive the same planner-visible actor label.

Ordinary event/effect/timing fields are held actor-independent in this theorem, following the observational-equivalence boundary proven by #1579. Only the trusted witness may split actor histories.

## Theorem

Exact deterministic classification into a requested taxonomy is possible from the witness iff every witness equivalence cell lies wholly inside one requested taxonomy cell; equivalently, the witness partition refines the requested taxonomy partition.

## Proof

Necessity: take any witness cell. A deterministic verifier sees the same witness value for every hidden actor in that cell, so it must emit the same output for all of them. If that cell intersects two requested taxonomy cells, those actors require different outputs, and one common verifier output cannot be correct for both. Therefore every witness cell must be contained in one taxonomy cell.

Sufficiency: if every witness cell is contained in one taxonomy cell, map each witness value to the unique taxonomy cell containing it. This deterministic map is correct for every hidden actor.

Thus actor claims cannot be finer than the equivalence relation induced by trusted provenance.

## Cardinality corollary

For exact identification of all five declared actor classes, each witness cell must be a singleton. The witness therefore needs at least five distinguishable states. A fixed-length binary encoding consequently needs at least three bits because two bits encode at most four states. This is only a cardinality lower bound: an unauthenticated or incorrectly scoped 3-bit field does not become trusted provenance merely because it has enough states.
