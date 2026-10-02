# #5895 T4 synthetic completion-semantics test

This is the separately allocated, one-shot T4 successor to the preparation and T3 STOP preserved in PR #5899. T3 is terminal; its output-volume mistake is not retried or rewritten. The exact T4 allocation, H/T/D/C/U, and frozen-source hashes are in [PREREG.md](PREREG.md). Recheck ownership, GitHub queue, source refs, OrbStack inventory, pinned image and empty output at the 10:30 UTC start gate described in [START_GATE.md](START_GATE.md).

Scope is one synthetic JSONL CLI: test whether the #5630 completion predicate admits Boolean `false`, float `0.0`, and a passing completion paired with a failing completion. Expected candidate exits are fixed at `[0,0,0,1,1,1,1,0]`; independent raw-only audit runs only after one candidate exit 0. No retry. This does not exercise X11, input, GUI, model, game, GPU, task effect or Issue #59's live threat-control exit condition.

The target files are read-only and source-bound to the exact blobs in PR #5630; the frozen source worktree is `origin/research/5895-auditor-completion-gate-prep-20261001` at the commit identified in the preregistration. The two container invocations use pinned `python:3.12-slim` linux/arm64, network disabled, read-only root/package/target, bounded resources and separate candidate/auditor roles. CID/stdout/stderr/inspect evidence stays in `results/formal-t4-01/receipts/`; only candidate artifacts are mounted at `/out`.

Host construction tests cover the literal eight-case matrix, typed-zero oracle, full artifact-inventory/hash auditor on a hand-built fixture, mutation detection, source identity checking, output non-overwrite, and frozen fixture import. These tests are preparation only; they do not execute the frozen target CLI matrix.
