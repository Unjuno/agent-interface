# Arena v1 local VLM grounding preflight — 2026-09-27

Issue: #4695. This is an exploratory construction/preflight, not a formal paired allocation and not a benchmark-retention result.

## H / T / D / C / U

- **H:** The local `qwen2.5vl:3b` visual model can read a task instruction and ground the named target to an actionable pixel center in Arena v1.
- **T:** One `full`-suite screen from frozen main `396a287588f8467d26a6b5cd75c75f6ef1468839`, seed 4695, difficulty 0.25. Same PNG, prompt, model digest, temperature 0, and 160-token output limit were sent once to the Windows Ollama service and once to a GPU-enabled local Ollama container. No game input was sent.
- **D (exploratory audit):** Semantic instruction must match the visible target, and the predicted center must fall inside the target pixels and the 720x520 screenshot. This criterion was applied during the post-run audit; it was not a preregistered formal benchmark gate.
- **C:** One static, public-generator Arena frame; Windows service was CPU-only while Docker service had a cold model load; not paired/counterbalanced; no Agent Interface input route or world-effect test.
- **U:** Generalization across seeds, primitives, held-out generators, other models, and any local refinement mechanism is unknown.

## Frozen inputs and provenance

Current main at evidence publication is `2983fbdf0a28a52beec0a91c013f65642b54e6be`. The Arena source blobs are unchanged from the tested source:
- `engine.py` Git blob `fb6dede4da31e0c2adc3d671932419f3f91e61e8`
- `arena.py` Git blob `f584551b5b629be61d64f576b3cd559e1737cd91`

The screenshot is retained as base64 in `arena-v1-frame.png.b64`; decode it to PNG before viewing. SHA-256: `24ae1b904c4742c21eee3855c2ea8c20a282786c461b0f0fdd1df0fe3600151e`; dimensions 720x520. The exact CPU-run JSON is retained as `cpu-result.json`.

Model: `qwen2.5vl:3b`, Ollama digest `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`, Ollama 0.34.4.

- Windows service: Ollama logs said “no usable GPU found” and “llama.cpp was compiled without GPU support”; the run used CPU. Inference wall time 51.622 s; prompt/eval tokens 1151/48.
- Local Docker GPU service: existing `ollama/ollama:0.34.4` image, image ID `8262851b2846`; RTX 3080 Laptop GPU passed through. Model cache was mounted read-only. `ollama ps` reported `100% GPU`; `nvidia-smi` observed 4235 MiB allocated. Inference wall time 78.92 s (reported model load duration 46.38 s); prompt/eval tokens 1151/48.
- The CPU/GPU wall times are **not a speed comparison**: runtimes, cold/warm cache state, and loading differ. The temporary GPU container was removed after the request; no model data was re-downloaded.

The first capture attempt failed before inference because no X display was started in the container (`ImageGrab.grab`: `OSError: X connection failed: error 5`). The corrected attempt started Xvfb and captured the frame. This infrastructure failure is retained here; it is not counted as a model result.

## Outcome and independent audit

Both model runs correctly read the instruction: `COMBO: hold SPACE and click the orange square.` Both identified stage `1/9`. Their coordinate predictions were:

| Backend | Predicted center | In bounds? |
| --- | ---: | --- |
| Windows CPU-only Ollama | [830, 640] | No |
| Local Docker Ollama, GPU placement | [920, 640] | No |

The screenshot's exact orange fill `RGB(249,115,22)` independently yields 2916 pixels, bounding box `(550,418)-(603,471)`, centroid `(576.5,444.5)`. Both predictions are outside the image and far from the target. The observer made no click, so there is no task-effect score.

**Decision: FAIL for direct VLM pixel-coordinate grounding in this single exploratory frame; HOLD for #4695.** This does not establish model quality generally or reject the benchmark. It shows this raw model response cannot safely be passed to an input tool without a separate validated grounding/refinement mechanism. The paired B0/C1 frontier, isolation, accounting, held-out composition, and cross-domain gates remain open.
