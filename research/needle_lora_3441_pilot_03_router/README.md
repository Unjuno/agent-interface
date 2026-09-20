# Needle skill-router successor — Issue #3441

This is a distinct, preregistered successor to pilot-02. It tests explicit per-skill dispatch and adapter snapshot round-trip/rollback.

## H / T / D / C / U

- **H:** Task-keyed dispatch preserves an old skill on the immutable base while a named LoRA adapter serves the new skill; stale/unknown route metadata yields.
- **T:** `runner.py` SHA-256 `BA70DBB0C65A1AAF9DFA1F0BFDCBF4247FC01F9409386F49A77B552BD4404505`; seed 3442; RTX 3080 Laptop GPU; PyTorch 2.5.1+cu121 / CUDA 12.1. Same synthetic task dimensions, 16 support rows, rank 2, 120 update steps.
- **D:** Scoped synthetic routing pass: routed old/new accuracy 0.9565/0.9565; globally applying adapter old/new 0.0327/0.9565. Four invalid route controls YIELD; base immutable; snapshot round-trip and rollback assertions passed. Update 150.0391 ms. Dispatcher-only p50 of five 200-call block means 0.000165 ms; this excludes inference/loading and is not end-to-end switching latency.
- **C:** Same generated task/seed/data/base and adapter; compare global application to explicit old->base/new->named-adapter dispatch.
- **U:** One synthetic seed. No GUI, image grounding, real action authority, multi-skill role graph, concurrent adapter writes, crash durability or broad generalization. Docker daemon was unavailable for this allocation; host GPU execution is not a container pass.

Rollback restored the pre-update adapter, whose new-skill accuracy was 0.0188; this confirms restoration mechanics but also shows rollback leaves the new skill unlearned. Do not treat this component result as a runtime/product pass.

See [RESULT.json](RESULT.json), [runner.py](runner.py), and [Issue #3441](https://github.com/Unjuno/agent-interface/issues/3441).