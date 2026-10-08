# Issue #8533 T0 A01 — tactic-inoculation vignette method check

## Scope and H / T / D / C / U

This executes the non-sensitive, no-participant T0 from [Issue #8533](https://github.com/Unjuno/agent-interface/issues/8533), based on current `main` `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. It validates vignette truth, arm parity, and holdout construction only. No person is trained or measured; T1 remains separately consented and unauthorized. Authority is `NONE`.

**H.** An independent truth reconstruction can distinguish verified scoped success, dispatch-only false success, partial effect, and UNKNOWN; training arms can receive equal factual evidence, feedback, word budget, and planned exposure time; and the test can preserve unseen layouts, receipts, exact examples, and a held-out persuasion tactic without exposing oracle labels.

**T0.** Construct 12 training examples and 16 test examples crossing four truth classes with three trained tactics and four test tactics. The test includes a tactic (`social_proof`) absent from training. Three synthetic arms receive the same claim/evidence/feedback, 80-word budget, and 60-second planned exposure; only the instructional treatment differs. Test prompts omit truth and tactic labels; a separate oracle table maps IDs to truth/tactic. A raw-only auditor derives truth from frozen effect receipts and verifies case/layout/receipt/example disjointness, exact arm parity, equal time/content budgets, tactic/truth balance, and the separate oracle join. Seven mutations test swapped labels, hidden evidence, layout leakage, UNKNOWN-to-success laundering, unequal exposure, test-oracle leakage, and authority inflation.

**D.** `METHOD_PASS_SCOPED` only if the auditor reconstructs all 12 training and 16 test cases; all four truth classes and the unseen tactic are present; no training/test case, layout, receipt, or tactic-example identity overlaps; all arms have identical factual evidence and verdict feedback with 80 words/60 seconds per item; test prompts disclose neither oracle nor tactic labels; UNKNOWN never becomes completed; and 7/7 mutations are rejected. Any truth, parity, or holdout error is `FAIL_METHOD`; an unscorable or custody failure is HOLD/STOP and receives no retry. One candidate and one auditor invocation, zero retries.

**C.** The truth cases and language are authored and deliberately simple. Equal word budget and planned time are metadata controls; they do not prove equal cognitive effort, accessibility, or actual reading time. Automated audit does not substitute for a blinded human review of ambiguity or tactic taxonomy.

**U.** This cannot estimate training benefit, delayed discrimination, false-acceptance/false-rejection rates in people, or transfer beyond these fixtures. No participant, model, real agent output, private material, account approval, live deception, or GUI is used. T0 method evidence does not imply H_PASS or authorize T1.

## Construction and formal gate

Construction tests and a separate temporary-output candidate/auditor replay must pass first. Freeze/push exact hashes and preregister on #8533; verify Issue and remote bytes before candidate invocation. Run the candidate once, hash its output, then run the independent auditor once only after candidate exit 0. Preserve the first result; no retry or post-freeze edit.
