# #8654 C01 — exact support/identifiability construction

**Type:** preregistered construction check, not the formal T0 allocation in Issue #8654. No result exists until the frozen candidate and independent auditor have run.

## Question
Can finite policy-selected feedback distinguish cue reversal from a global outcome shift only when each context/action cell has observed support, and otherwise return UNIDENTIFIABLE? This isolates the issue's support boundary; it does not test learning, noise, propensity misspecification, future-information leakage, or human/GUI behavior.

## Frozen finite fixture
Two equiprobable contexts; two already-qualified actions per context. The cue-favored action is A in context 0 and B in context 1. Each context has 16 trials. Under the diagnostic policy, each trial selects the cue-favored action with probability 0.75 and the alternative with probability 0.25, independently and with known propensity. Enumerate the exact binomial-count distribution; do not draw random samples.

Potential outcomes (same in both contexts): stable (cue=1, alternative=0); reversed cue (0,1); stable mapping with global shift (0,-1). Thus greedy cue-only feedback sees the same zero on reversed/global-shift worlds and cannot identify which occurred. Full potential outcomes are oracle-only.

For each of the 3 regimes × 17 alternative-count values per context × 17 alternative-count values per context, compute exact joint probability, support, Horvitz–Thompson means with the frozen known propensities, contrast, and decision. Require positive observed count for both actions in each context; else return UNIDENTIFIABLE. With complete support: contrast < 0 => REVERSAL; otherwise cue mean > 0.5 => STABLE; otherwise GLOBAL_SHIFT. Contrast equality at 0 is a method failure (none is expected in the finite fixture). Baseline GREEDY_CUE_ONLY has zero alternative support in both contexts and must return UNIDENTIFIABLE in all regimes.

## H / T / D / C / U
- H: The diagnostic design has positive probability of complete support and correctly classifies all three deterministic regimes on every supported count tuple; unsupported tuples remain explicitly unidentifiable. Greedy cue-only feedback cannot separate reversal from global shift.
- T: Run frozen candidate.py once to produce JSONL; run frozen audit.py once as an independent raw-only reconstruction. Exhaustively cover 867 rows. Auditor checks row identity/uniqueness, binomial probability, support, HT estimates, oracle contrast, classification, greedy baseline, probability mass, and four in-memory mutation controls.
- D: PASS_CONSTRUCTION_SCOPED iff candidate emits exactly 867 unique rows; each regime's mass is 1 within 1e-12; all values and labels match independent reconstruction; greedy is unidentifiable for all regimes; and 4/4 mutations are rejected. Otherwise FAIL_CONSTRUCTION or HOLD_AUDIT.
- C: If the prescribed estimator/classifier separates no better than greedy, either chosen-action outcomes already identify the regimes or additional action support adds no useful information in this fixture.
- U: Deterministic potential outcomes, two contexts/actions, known propensities and reset-independent trials are idealizations. This does not validate the complete #8654 proposal, any learner, empirical benefit, GUI effect, user preference, or safe exploration.

## Execution/evidence
Frozen source path: this directory. Pure Python standard library only; no model, GUI, external effect, network, GPU, or container boundary is needed. The attempted WSLc container smoke test timed out in a previous readiness check; the registered Ubuntu distro also currently fails process startup, so this construction uses the available native Windows Python host. Host-only execution does not establish WSLc parity or resource enforcement. Preserve the first outcomes; no reruns or threshold edits.
