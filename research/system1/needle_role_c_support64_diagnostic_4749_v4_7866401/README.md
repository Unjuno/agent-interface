# Successor to #4848 — paired role-C support diagnostic, seed 7866401

One paired synthetic support16/control versus support64/treatment diagnostic against the frozen #4749 main runner. It is not a rerun of #4848's consumed seed and cannot alter #4749's completed ten-seed result.

## Provenance and preflight

`upstream_runner.py` is byte-identical to the #4749 main runner (Git blob SHA-1 `ecd3a0414178f38535406573314793a40b353878`). `prefix_contract.py` is shared by the zero-training construction check and formal runner. It compares shapes, dtypes, `torch.equal`, and flattened contiguous uint8 bytes. The construction test validates a sentinel serialization and rejects a mutated prefix; it also parses all executable sources. Result: `CONSTRUCTION_PASS`, seed 7866401, zero optimizer updates.

## Formal plan

One orchestration only, local `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU; `--pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64`, frozen source read-only, dedicated output volume. Train the base for 400 updates, B for 120 invariant-control updates, and each C arm for 120 updates. No retries or substitutions.

Separate raw-only auditor imports neither the upstream trainer nor paired runner; it reconstructs six role predictions and labels, the 16-row prefix, A/B invariance and C delta from serialized inputs/state.

## Scope

Even a valid result is one descriptive synthetic point. It establishes no online real-time learning quality, GUI/task transfer, concurrent-update quality, natural-skill transfer, production readiness, or action authority. See `PREREGISTRATION.md` and `FORMAL_RESULT.md`.

