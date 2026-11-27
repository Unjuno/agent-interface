# Issue #8636 T0 A04 — formal outcome

Disposition: **HOLD_UNCERTAIN**. The 360-trial candidate process completed once, but the one-shot independent auditor exited 1 before writing a summary. No hypothesis result is admissible and no retry was made.

The first audit failure, in event order, is `feature_loss-30090-viewstate_oracle`, step 0. The injected `near_singular` fixture is detected as ambiguous/missing landmarks, so the runner records `YIELD` (`landmark missing or ambiguous`) for the oracle arm. The auditor explicitly assumes the viewstate-oracle arm cannot yield, despite the runner calling the same image detector before branching to the privileged-state action. This is a harness/arm-boundary mismatch. It cannot be repaired after the frozen one-shot execution by rerunning this allocation.

A second pre-audit check of A03's focal reason is not the failing first row: A04 candidate emits `feature shape changed`, and the frozen independent reconstruction predicts that exact reason for its focal-shape abstention. This local counterexample regression passed in both normal and optimized construction suites. That does not establish a successful whole-run audit.

No posterior counts, performance comparisons, hypothesis support, or method-scoped inference should be taken from `scorer_truth.jsonl`; those candidate-supplied fields are not accepted without the independent audit. This execution does establish a concrete design contribution: an oracle arm intended to provide explicit ViewState must not depend on the candidate image detector, or its semantics and auditor must explicitly account for perception-driven abstention. A future test must implement that correction under a fresh allocation and preregistered freeze.

## Invocation and custody

- Frozen source commit: `2f15e4f9a68cea4b9e47940b8f9b468ba5dd07cf`, based on main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- Candidate: one invocation, 2026-10-12 02:18:47.2531656–02:18:55.3904552 UTC, exit 0; emitted 360 trials.
- Auditor: one invocation, 2026-10-12 02:19:19.9697971–02:19:32.5028000 UTC, exit 1; no retry.
- Raw tree: 2,198 files, 62,552,757 bytes; 360 truth rows and 2,555 event rows.
- Archive: `A04-first-outcome.tar.gz`, 335,880 bytes, SHA-256 `631b987c8184f2fd75be32fb06f9acee9ae59a504cdd441e3fbdb1508d9e945e`.
- Manifest: `A04-raw-manifest.json`, SHA-256 `7c75014da1f1581461381238d6c93178bfbf395391874b49aeb032670cf68a6f`.
- Independent custody check: all 2,198 archive regular files match the manifest byte count and SHA-256; no missing, extra, or mismatched files.
- Auditor stderr SHA-256: `f83d713dd7b5e507e4339ea603e3a4f041f361b9601a67fe8971e9209b9887a0`; stdout empty. No `audit.json` was produced.
- Scope: local deterministic synthetic CPU fixture only. No WSLc, container, GUI, game, model, OS input, external service, or live effect.

The result does not justify merging a controller method. Preserve A04 as a failed audit allocation, correct the oracle boundary and independent replay design, then seek a new allocation only after checking ownership and overlap.
