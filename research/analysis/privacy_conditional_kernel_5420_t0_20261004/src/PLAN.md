# 5420 conditional-kernel admission T0 — preregistered protocol

## H / T / D / C / U

**H.** A gate that evaluates the next release's exact conditional kernel given the recipient-visible history and shared-randomness lineage rejects a shared-pad second release, while admitting a fresh-independent-pad and a constant-output zero-disclosure control. A marginal-only accountant incorrectly admits the coupled pair.

**T.** Exhaustively enumerate three exact binary mechanisms, no sampling:

1. Shared pad: `S,R ∈ {0,1}`, `A=R`, `B=R XOR S`.
2. Fresh independent pad: `S,R,R' ∈ {0,1}`, `A=R`, `B=R' XOR S`.
3. Constant control: `S,R ∈ {0,1}`, `A=R`, `B=0`.

The same recipient sees ordered history `(A,B)`. Compare marginal-only release accounting with a candidate conditional-kernel gate. Retain every full latent/input/output row, randomness lineage, recipient-visible prefix, exact conditional distributions, both decisions, and refusal reason. The independent auditor reconstructs all rows/kernels from this source spec and raw output without importing the candidate.

**D.** `PASS_METHOD_SCOPED` only if the shared-pad conditional supports are disjoint across neighboring secrets (therefore the second release cannot meet any finite ε at δ<1), the fresh-pad and constant controls have identical conditional output distributions across secrets and are accepted as zero-disclosure in this finite mechanism model, the marginal-only comparator accepts the shared pair, and the raw-only auditor rejects all four preregistered mutations. False acceptance/rejection or a missed mutation is `FAIL_METHOD`. Unknown history/randomness lineage is `UNKNOWN_KERNEL/HOLD`. These are exact finite-channel properties, not an arbitrary-UI DP claim.

**C.** A mechanism whose guarantee composes for every permitted prior transcript needs no extra gate; restricting one recipient from obtaining both releases is a distinct access-control solution but is not this same-recipient test.

**U.** Three exact binary channels only. No finite-sample estimate, actual screenshot/UI mechanism, timing channel, consent behavior, multi-recipient collusion, provider knowledge, or production privacy guarantee. Conditional Shannon information is not ε-DP.

## Lineage / prior art

This is the unverified conditional-kernel refinement in Issue #5420, not a rerun of its T1 randomized-response experiment (merged PR #5445), #6201's metadata result, or the previously enumerated XOR truth table. The exact counterexample is known prior art: Kawamoto, Chatzikokolakis & Palamidessi, [On the Compositionality of Quantitative Information Flow](https://arxiv.org/abs/1611.00455), §2.2/Prop. 30; Whitehouse et al., [Fully-Adaptive Composition in Differential Privacy](https://proceedings.mlr.press/v202/whitehouse23a.html), defines privacy filters/odometers under adaptive mechanisms and parameter choices. These sources motivate the eligibility question; this finite fixture is not itself a DP mechanism proof.

## Frozen execution boundary

- Allocation: `5420-COND-KERNEL-T0-01`.
- Repository source base: `c7837e7aae09bf2f3d9b40a77b790d7d6777d799`.
- Runtime: OrbStack Docker, Node image pinned by manifest digest in `raw/freeze.json`; formal containers use `--pull=never`, `--network=none`, read-only `/src`, separate `/out`, and do not mount any user data.
- Formal sequence: one candidate invocation, then one independent raw-only auditor invocation. Construction/unit tests do not emit formal result files. Any formal STOP/FAIL is retained; no candidate retry.

