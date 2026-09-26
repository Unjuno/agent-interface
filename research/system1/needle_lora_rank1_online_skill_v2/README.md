# Rank-1 online LoRA skill update — allocation v2

Issue: [#4507](https://github.com/Unjuno/agent-interface/issues/4507). Allocation 01 is retained as a pre-training STOP in the sibling v1 directory and is not altered or pooled.

This fresh allocation evaluates the same paired rank-1/rank-2 online adaptation hypothesis on a fresh seed block. The frozen v1 trainer and auditor are mounted read-only; v2 wrappers alter only allocation identity, seeds, and output placement. The host creates `/out/training` before writing root invocation metadata, so the runner's empty-directory precondition remains true.

- Contract: `PREREGISTRATION.md` and `PREREGISTRATION.json`
- Entrypoints: `runner_v2.py`, `audit_v2.py`, `formal_v2.py`
- Construction checks: `test_construction_v2.py`
- Frozen dependencies: `../needle_lora_rank1_online_skill_v1/runner.py` and `audit.py`

No runtime/product code, user data, real feedback, GUI, provider call, or action authority is involved.
