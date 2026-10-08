# Marginal local cost of the second speculative branch — first outcome

Decision: `PASS_SECOND_BRANCH_COST_BELOW_K2_ADVANTAGE_SCOPED`.

This source-first formal uses the exact current retained `prepare_program.py` and `receipt_image.py` implementations from BASE `bf42df14fa3620c340df7b70bb837a0699c582c5`. The only compared factor is branch count: K1 prepares one no-authority program; K2 prepares two independent programs from the same received evidence. Each branch is charged current evidence/image validation and SHA-256, strict step copy, command creation, canonical JSON serialization, JSON decode, independent structural validation and bounded in-memory retention. Socket send, runtime admission, model generation and GUI/task effect are excluded.

After 20,000 warmup pairs, the one formal invocation retained 100,000 alternating-order paired iterations:

- K1 p50 **0.052930 ms**, p95 **0.085990 ms**, p99 **0.162485 ms**;
- K2 p50 **0.105730 ms**, p95 **0.166260 ms**, p99 **0.298770 ms**;
- paired marginal K2-K1 p50 **0.052169 ms**, p95 **0.104828 ms**, p99 **0.219330 ms**;
- K1/K2 retained encoded command bytes **233 / 466**, exactly 1 / 2 branch objects;
- semantic controls 7/7; authority/socket/model/GUI/task-input actions 0.

The frozen comparison boundary from #1127/#1153 is **7.82655 ms**, the observed absolute temporal K2-vs-K1 mean-latency advantage before branch-preparation cost. Charging the measured second-branch local cost leaves:

- **7.774381 ms** advantage after the paired median marginal cost;
- **7.721722 ms** advantage even after the paired p95 marginal cost.

Therefore the current local deterministic preparation path does not justify preferring K1. In this scoped synthetic planner-gap comparison, **K2 remains the performance baseline** unless a later measurement finds substantial planner/model branch-content generation cost or runtime admission cost not included here.

The result is intentionally conservative for local preparation because the current API resolves and hashes the same image independently for each branch. A shared-evidence implementation could reduce this cost further. Conversely, this result says nothing about the cost for Astra/frontier model to author an additional semantic branch.

Integrity: exact source archive SHA-256 `00cc72bb24c6a562a3b12f5b5ab0147758e54fbbea561a323767258e828b1e1e`; formal RESULT SHA-256 `526381f7802d4682370177ec65f89f373984d3a11c973daf1beb1cb2ab9ddf88`; exact raw JSON SHA-256 `412af339d3145f7b0b8b4b9475e5735fd4070314a97f18e25d91517d4418bb3b`; source rehash exact; copied-result/raw corruptions 5/5 rejected; formal invocation1/reruns0.
