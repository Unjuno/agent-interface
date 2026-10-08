# Issue #8654 C02 — finite-sample support sufficiency and raw-custody successor

**Allocation:** C02, a new successor allocation to C01. C01's STOP_RAW_CUSTODY_NOT_RETAINED and its original source/results are immutable and remain in draft PR #8659. C02 does not reuse or rewrite C01's raw output.

## Question and H/T/D/C/U

**H — falsifiable hypothesis.** Complete observed action support is not sufficient to guarantee correct cue-regime classification for every positive-probability finite realization under the frozen Horvitz–Thompson threshold rule. In the stable regime, at least one fully supported tuple will be labeled GLOBAL_SHIFT because the finite-sample HT cue mean is at or below the strict 0.5 threshold.

**T — frozen test.** Use two equiprobable contexts, 16 trials per context, two already-qualified actions, and known alternative-action propensity p=0.25. Enumerate exactly all 17×17 binomial count tuples for three deterministic regimes (STABLE: cue=1/alternative=0; REVERSAL: 0/1; GLOBAL_SHIFT: 0/−1), plus one explicit GREEDY_CUE_ONLY baseline row per regime. Diagnostic-world weight is Binom(16,k0;0.25)×Binom(16,k1;0.25); total opportunity count stays fixed. Estimate each action mean with the frozen HT formula, require both actions in each context for identification, then classify: UNIDENTIFIABLE without complete support; REVERSAL if cue-minus-alternative <0; otherwise STABLE if cue HT mean >0.5; otherwise GLOBAL_SHIFT. Candidate writes JSONL to an exclusive new file, flushes/fsyncs the file and directory, hashes and sizes it, and emits a receipt. A GitHub Actions artifact upload of raw JSONL+receipt must succeed before the auditor step is allowed to run. The independent auditor reads raw JSONL only, reconstructs every row and aggregate from this protocol, and tests five frozen in-memory corruptions. One candidate invocation and at most one auditor invocation; no retries.

**D — decision.** PASS_METHOD_SCOPED iff 870 unique rows (867 diagnostic + 3 greedy) reconstruct exactly, diagnostic probability mass is 1 per regime within 1e−12, baseline rows all abstain as UNIDENTIFIABLE, every aggregate recomputes, and 5/5 corruptions are rejected. Separately report the exact probability mass and conditional-on-support accuracy of each classifier/regime. COUNTEREXAMPLE_TO_SUPPORT_SUFFICIENCY_SCOPED iff a positive-probability fully supported tuple is misclassified; otherwise NO_COUNTEREXAMPLE_AT_DECLARED_GRID. Candidate/audit disagreement is FAIL_METHOD. If raw is not durably uploaded before audit, record STOP_RAW_CUSTODY_NOT_RETAINED; do not run the auditor or retry.

**C — competing explanations.** The finite-sample HT estimate can cross a decision threshold despite positivity; the strict classification threshold, rather than lack of support, may explain errors. Greedy abstention may be preferable to a noisy identified estimate. A global-reward change and cue reversal remain distinct regimes under this fixed fixture.

**U — limits.** This deterministic one-step finite method probe has no stochastic rewards, propensity misspecification, sequential carryover, agent learning, GUI, user, external effect, or deployment. It tests neither empirical benefit of exploration nor the full Issue #8654 proposal. It cannot establish a runtime policy or authorize diagnostic actions.

## Provenance and execution boundary

Base main observed before freeze: 9f67de666b640997ed7cb27cbe278ef19677be5d (2026-10-08). Candidate, auditor, finalizer, protocol, and workflow are frozen together by the source commit recorded in results/EXECUTION.json. Execution uses one GitHub-hosted ubuntu-24.04 CPU runner with Python 3.12.10, standard library only; no WSLc/Docker command, model, GUI, network data input, GPU, or user action. Raw artifact is uploaded before independent audit and the final raw/audit/receipt/report are committed additively under results/.

No performance, memory, Docker parity, WSLc parity, production or safety claim follows.
