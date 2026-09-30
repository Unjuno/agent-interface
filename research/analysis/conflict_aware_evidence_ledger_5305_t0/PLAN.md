# Conflict-aware evidence ledger — T0 finite discriminator

Issue: [#5305](https://github.com/Unjuno/agent-interface/issues/5305)
Parent: #5267. This is a deterministic analytical/construction rung, not the
held-out GUI trace comparison in the Issue.

## H — hypothesis

For one proposition with explicit freshness and independence metadata, a
support/refutation ledger distinguishes (a) ignorance, (b) stale-only evidence,
(c) fresh contradiction, and (d) fresh agreement. Exact duplicate or
same-independence-group support does not accumulate. A conservative projection
never turns missing, stale-only, or contradictory evidence into PASS.

## T — frozen finite model

Enumerate every non-empty subset of five frozen evidence atoms:

| Atom | Sign | Fresh | Independence group |
|---|---|---|---|
| `s1` | support | yes | `g1` |
| `s1dup` | support | yes | `g1` |
| `s2` | support | yes | `g2` |
| `r1` | refute | yes | `g3` |
| `sold` | support | no | `g4` |

The 31 subsets cover independent agreement, exact/same-group duplicates,
stale-only and stale+fresh evidence, missing sign, and fresh contradiction.
Compare a candidate lattice projection with a separately coded oracle. Also
compare against a deliberately lossy ternary reducer and count cases where a
fresh conflict collapses into ordinary uncertainty. Mutation controls alter
one candidate sign, one freshness bit, duplicate grouping, and conflict output;
the checker must reject every mutation.

## D — frozen decision gates

- `PASS_T0_FINITE_MODEL`: all 31 candidate states equal the independent oracle;
  no support inflation from same-group duplicates; fresh support+refutation is
  `CONFLICT`; stale-only is `UNCERTAIN`; all four mutation controls reject.
- `FAIL_LEDGER_INVARIANT`: any semantic mismatch or duplicate inflation.
- `STOP_INTEGRITY`: source/result hash or mutation-control integrity fails.

This is an exhaustive finite model result, not a probability estimate.

## C — competing explanations

If the runtime contract guarantees globally unique independent receipts, or if
freshness/independence metadata is not trustworthy, the added state may be
redundant or unsafe. A two-bit support/refutation lattice may be simpler than
belief masses; this T0 deliberately avoids calibrated probability/mass claims.

## U — scope

No retained GUI traces, model, GPU, action, verifier correctness, calibrated
belief mass, scheduler behavior, latency, unsafe-admission rate, or human review
is tested. Same-author independent oracle code is not independent review.
Evidence independence is trusted fixture metadata only.

## Execution freeze

- Base `main`: `02bff58173426efc2288bd375f283a6500f80784`
- Branch: `research/conflict-ledger-5305-t0`
- Path: `research/analysis/conflict_aware_evidence_ledger_5305_t0/`
- Runtime: host Python standard library only; no Docker, network, model, GPU,
  GUI, or external state. This is a finite exhaustive model check; the research
  method calls for analytical enumeration when semantics are fully specified.
- Exactly one candidate run and one separately implemented raw audit; no retry.
- No predecessor evidence is edited.
