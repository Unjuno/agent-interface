# Complementarity stress test for marginal evidence stopping — T0 plan

Issue #5869; this finite model-free simulator extends the issue's earlier four-world analytic calibration (comment #5926254207) into a nine-case policy comparison. It freezes the question and decision gates before the single formal candidate invocation.

## H / T / D / C / U

**H.** There exists a preregistered finite interface-evidence class where a myopic positive-marginal rule stops although a feasible two-check bundle has positive net decision value, while a bounded complementarity gate recovers useful correct decisions without worsening forbidden-effect or freshness outcomes. Whether real GUI/verifier traces contain this class is unknown.

**T.** Enumerate nine finite cases over fixed weighted worlds: balanced XOR complementarity; redundant duplicate signals; independent noisy observations with diminishing returns; a pair whose cost exceeds its joint value; a pair that misses the deadline; mismatched epochs; shared source/failure domain; failed mandatory gate; and a perfect one-bit signal with only 0.05 expected decision-loss reduction against a 0.06 query cost. Compare a fixed checklist, one-step marginal VOI, exact two-step adaptive Bellman, and a bounded pair gate. Keep worlds, loss tables, cost units, source identities, epochs, freshness, budgets, and deadlines identical across policies. Candidate emits policy trees and claims; independent raw-only auditor scores every leaf and exhaustively enumerates every feasible depth-two policy. No model, GUI, application, external effect, CUDA, or live trace is used.

**D.** PASS_METHOD_SCOPED only if the pair gate selects the XOR pair where each singleton has zero value, the exhaustive two-step oracle improves over myopic on that control, and rejects redundant, costly, late, stale, same-source, failed-gate, and low-decision-value cases; the myopic rule uses only positive marginal value; every candidate claim matches independent recomputation; the mandatory gate is never bypassed; and mutation controls are rejected. A test or audit discrepancy is FAIL_AUDIT; otherwise retain HOLD_UNIDENTIFIABLE if the fixture cannot distinguish complementarity from dependency/freshness or authority.

**C.** All worlds and probabilities are authored synthetic inputs. The test measures decision-loss value, not information bits alone. The commit/decline outputs are recommendations in a no-effect simulator and do not grant interface authority. Source IDs and epochs are declared fixture fields; they are not discovered from real GUI receipts.

**U.** This finite construction cannot establish that real observations exhibit synergy, that a two-check gate improves live GUI correctness/latency, that loss/cost calibration transfers, or that depth greater than two is unnecessary.

## Frozen case schedule

Nine cases, all attempts represented:

1. xor-complementary: the four equally likely XOR worlds from the analytic calibration. Each singleton has zero decision value. Per-check cost 0.1 gives pair net value +0.8.
2. redundant-duplicate: either one check determines target; pairing adds no decision value.
3. diminishing-returns: two independent 0.8-accurate checks, per-check cost 0.16.
4. pair-too-costly: XOR pair cost 0.6 each; total cost 1.2 exceeds unit decision value 1.0, so pair net value is −0.2 even though joint information is one bit.
5. pair-too-late: XOR checks each take 8 ms; combined deadline is 10 ms.
6. epoch-mismatch: XOR signals have different evidence epochs.
7. shared-source: XOR signals share one declared failure-domain/source identity.
8. mandatory-gate-failed: XOR case with the mandatory gate closed.
9. one-bit-low-decision-value: perfect one-bit check; expected loss falls by only 0.05 while query costs 0.06.

Construction sensitivity controls mutate a world probability, an abstention-loss value, and both XOR check costs. The frozen fixture and source hashes are in FREEZE.json. Formal candidate and separate raw-only audit are each invoked once after the GitHub readback freeze. No retries or tuning.
