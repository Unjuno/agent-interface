# Rank-1 online LoRA skill update — allocation v2

Issue: [#4507](https://github.com/Unjuno/agent-interface/issues/4507). Allocation 01 is retained as a pre-training STOP in the sibling v1 directory and is not altered or pooled.

This fresh allocation evaluates the same paired rank-1/rank-2 online adaptation hypothesis on a fresh seed block. The frozen v1 trainer and auditor are mounted read-only; v2 wrappers alter only allocation identity, seeds, and output placement. The host creates `/out/training` before writing root invocation metadata, so the runner's empty-directory precondition remains true.

- Contract: `PREREGISTRATION.md` and `PREREGISTRATION.json`
- Entrypoints: `runner_v2.py`, `audit_v2.py`, `formal_v2.py`
- Construction checks: `test_construction_v2.py`
- Frozen dependencies: `../needle_lora_rank1_online_skill_v1/runner.py` and `audit.py`

No runtime/product code, user data, real feedback, GUI, provider call, or action authority is involved.


## Formal disposition

**FAIL_RANK1_SKILL_CAPACITY**. Independent audit passed with zero integrity errors, but one of three rank-1 held-out accuracies missed the 0.90 per-seed floor (seed 74333: 0.894287). Rank-1 update-only p95 was 2.254438 ms versus rank-2 2.208662 ms over 48 measurements (ratio 1.020726), missing the preregistered <=0.80 speed-benefit gate. One formal Docker invocation, zero retries/substitutions/post-result tuning. Full raw per-seed results and logs are in `formal/alloc-02/RAW_TRAINING.zip` (SHA-256 `7a739e80b282cbe8943f4b1897bbde0c7373d7a55cd1d4823e99abe9ca4a65e3`). This is synthetic online adaptation, not a real pretrained Needle/production real-time fine-tuning result or role-network composition result.
