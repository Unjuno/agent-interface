# Issue #5516 T12 — branch readiness is not visible-trace equality

## Disposition

`PASS_BRANCH_READINESS_METHOD_SCOPED`. In one frozen, finite, tau-free LTS
witness, the two systems have identical complete visible trace sets but are not
strongly bisimilar: their legal next-action sets differ after the shared
`OPEN` prefix. The independently derived raw-only audit found the two
post-`OPEN` branch witnesses. This supports using a branching relation when
substitutability requires per-state continuation availability; it does not
show that every interface equivalence contract needs bisimulation.

## Frozen experiment and execution

- Issue: [#5516](https://github.com/Unjuno/agent-interface/issues/5516),
  T12 allocation `5516-branch-readiness-context-t12-20261001-01`.
- Base: `e32ace71fa1158ca8d5eec13fe620a1a51c1ff00`.
- Host: CPython 3.14.5, standard library; no network, container, GUI, model,
  or external effect. This finite model was run outside Docker because the
  repository's shared OrbStack provenance/assignment hold remains unresolved
  in #5085. It is not reported as container evidence.
- Candidate invocation: 1, exit 0; no retry or tuning.
- Independent raw-only audit: 1, exit 0; 3 rows, `PASS`, zero errors. It
  recomputed trace sets and the greatest strong-bisimulation relation from
  graph edges, without importing candidate code, and reported:
  - `copy_branch` vs `combined_branch`: right-only action `DELETE`;
  - `delete_branch` vs `combined_branch`: right-only action `COPY`.
- Corruption controls: 7/7 rejected (duplicate/missing case, forged
  bisimulation summary, deleted edge, renamed edge, out-of-model cycle, forged
  trace list).
- Construction tests after the pre-freeze correction: 4/4 PASS. The initial
  3/3 construction failure and its trace-enumerator diagnosis are preserved
  in `CONSTRUCTION_NOTES.md`; no candidate CLI was run before correction.
- Validation command note: one combined post-run check was first invoked from
  the package directory while using repository-root-relative paths; its
  checksum step passed but the later path lookups failed. The same scoped
  validation was then run from the worktree root and passed. This was a
  command-working-directory error, not a candidate/audit result.
- The final checksum-manifest verification was also once invoked from the
  worktree root even though manifest paths are package-relative; those path
  lookups failed without changing any artifact. It is being verified from the
  package directory, where the manifest's relative paths resolve.

## Case outcomes

| Case | Same visible trace set | Strongly bisimilar |
|---|---:|---:|
| Exact positive control | yes | yes |
| Branch-readiness split | yes | no |
| Visible-label mismatch (`DELETE` / `ARCHIVE`) | no | no |

The branch-split is a distinguishing witness against trace-set equality as a
substitutability test when an action's legality depends on the current hidden
branch. It does not establish that `COPY` or `DELETE` is unsafe; it establishes
that the systems expose different continuation choices after the same prefix.

## Reproduction and hashes

See `PLAN.md` and `FREEZE.json` for H/T/D/C/U, frozen source identities, and
the exact one-shot commands. Retained raw SHA-256:

- candidate JSONL: `07b25c33dc143485e51162dbdc10ab3d181b2934cafe89964315c5713170474d`
- audit JSON: `717831b221e7b5c77fac7a4ed802b9cec38794194c58567002bbd5fc0da5eb1f`
- corruption controls JSON: `64929879cf3fe5762822f956ad1d1a306559a9e7e235108a5f2c9d761512b803`

## Scope and residual

This is a hand-authored finite semantic counterexample, not an adapter or GUI
observation. No partial observation, tau transition, divergence, timing,
external effect, authority, task completion, latency, reliability, or product
equivalence is evaluated. The useful follow-up is to define the actual
observation alphabet and test whether agent-relevant next-action availability
is contract-visible in retained adapter traces. Issue #5516 remains open.
