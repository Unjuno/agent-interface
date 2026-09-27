# Issue #4885 — aligned edge auxiliary view (R8)

This is a successor experiment under #570. It compares the exact same dense synthetic settings screenshot as (A) one RAW image and (B) the RAW image plus one pixel-aligned deterministic grayscale edge view. The second image can inform geometry only; image 1 and its coordinates remain authoritative. No live GUI, click, training, or model authority is involved.

## Frozen design

- **H:** On fresh dense synthetic application screens with small repeated controls, the edge auxiliary view preserves RAW's positive target-region hits and absent-target abstentions and reduces mean normalized point-to-target-region distance by at least 0.05.
- **T:** 10 positive and 2 absent formal screenshots at 1280x800; exact Arial 10 px card text, repeated Archive controls, and near-duplicate card titles. Two separate construction screens use seeds 5708811–5708812; formal screens use 5708821–5708832. Only the visual input arm changes. Prompt bytes, model, seed, decoding, source screenshot, target rectangle, and paired counterbalance are fixed.
- **D:** A positive is a returned integer point inside the inclusive frozen target rectangle. An absent abstention is exactly `present=false, point=null`. Region error is distance to the nearest target-rectangle point divided by the 1280x800 image diagonal. The audited gate is `PASS_EDGE_AUX_SCOPED`, `REJECT_EDGE_HURTS_CORRECTNESS`, or `REJECT_NO_MATERIAL_EDGE_GAIN`; malformed/provenance/GPU evidence is HOLD/STOP.
- **C:** Local Windows RTX 3080 Laptop; cached Ollama 0.34.4 and Qwen2.5-VL 3B Q4_K_M. A new Docker internal network hosts the GPU-enabled Ollama service, whose model directory is read-only; the request helper is GPU-less and the independent auditor is CPU-only/networkless. The existing R3 Ollama container is not modified. The only screens are generated synthetic data.
- **U:** One synthetic layout family, one local model/GPU, ten positive and two absent examples. No real-app transfer, semantic identity, click safety, calibration, general vision benefit, latency savings, or runtime/product readiness claim.

## Evidence workflow

`src/build_inputs.py` generates the source PNGs and the aligned `Pillow FIND_EDGES` views. `src/runner.py` issues exact one-shot paired requests and retains the request bytes, response, timestamps, and Ollama placement receipts. `src/audit.py` is an independent raw-only scorer; it recomputes the edge transform and audits source/prompt/model/options/order/GPU overlap before scoring. `src/run_local.py` starts only uniquely named internal Docker resources, runs a disjoint construction pair first, executes the formal block once only after construction audit PASS, audits it in a separate GPU-less container, and stops/removes only its own service/network.

Local Docker construction tests:

```text
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m -e FONT_PATH=/font/arial.ttf --mount type=bind,source=<src>,target=/src,readonly --mount type=bind,source=<inputs>,target=/inputs,readonly --mount type=bind,source=<arial.ttf>,target=/font/arial.ttf,readonly --entrypoint python agent-interface-real-robustness-2912:cpu -m unittest discover -s /src -v
```

The six tests cover split/dimension/edge alignment, exact valid paired audit, missing call, swapped edge bytes, altered prompt, and absent GPU overlap. Formal command is `python src/run_local.py`, after the exact committed source and inputs have been read back from GitHub and `FREEZE.json` is final. There are no retries or substitutions.

The formal result and raw bundle will be appended under `results/` and published losslessly with hashes. Any negative result remains a scoped result under #570 and does not alter earlier ladder or temporal outcomes.
