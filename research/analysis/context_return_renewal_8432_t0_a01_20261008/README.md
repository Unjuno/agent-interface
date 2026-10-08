# Issue 8432 — context-return renewal T0 A01

## H / T / D / C / U

H: In this deterministic finite assay, returning to context A after an A→B cue–outcome reversal is distinct from continuing in B or entering C, while the active mapping remains B. A context-tagged advisory ledger may change representation/applicability only and must preserve the same source examples. This is a method hypothesis, not an LLM renewal claim.

T0: Materialize the frozen acquisition/correction/test/return tracks and matched controls; independently reconstruct episodes, support, counts, mapping transitions, recurrence, and regret. Reject the frozen test-mapping-leak, phase-erasure, context-relabel, and mapping-change mutations. Candidate and auditor each run once. No model, GUI, game, OS input, or external network.

D: PASS_METHOD_SCOPED only if raw exactly matches the frozen protocol; 12 matched history-treatment × context-track episodes preserve cue/action/outcome support and counts; current mapping remains B for tests; the no-signal scorer control is equal across contexts; seeded recurrence/regret is higher only for A-return than B/C; and all four frozen mutations are rejected. Otherwise retain the first FAIL/STOP; no retries.

C: T0 validates construction and scoring, not model behavior. Seeded proposal traces are code-path controls, not observations. Context tags could prime a model; an explicit ledger could change prompt length or recency.

U: Whether a fixed model learns the association, adapts in B, renews in A, or benefits from tagged history remains unknown. No generalization, GUI, human-learning, safety, efficacy, or product claim follows.

## Source and scope

This is the CPU-only method rung of [successor Issue #8432](https://github.com/Unjuno/agent-interface/issues/8432), a context-return follow-up to [#8200](https://github.com/Unjuno/agent-interface/issues/8200). It does not alter #8200 A01 STOP / PR #8208 or authorize the separately gated model study. The animal-learning papers cited by #8432 provide structural analogy only.

## Frozen reproduction

Candidate: `python3 -B candidate.py` exactly once.
Independent auditor: `python3 -B auditor.py` exactly once; one pass includes all frozen mutation controls.
Runtime: Ubuntu WSL, Python 3.12.3, WSL package 3.0.1. No Docker daemon, model, GUI, or network during execution.
Source commit and protocol/candidate/auditor hashes are pinned in `FREEZE.json`.
First outcome is final. No candidate rerun or retry.

Result: PENDING (not yet executed).

