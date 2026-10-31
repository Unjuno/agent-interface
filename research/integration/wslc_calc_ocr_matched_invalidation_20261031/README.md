# WSLc Calc: matched OCR after invalidated reference

Two preregistered single-attempt runs use the same fixed Calc fixture, image, mounted source, actual Tesseract fixed-crop rule, known expected values and guarded Save. The compiled arm ran first with an intentionally stale 731/864 pixel reference; its first entry returned `SAFE_YIELD` and was not replayed. It captured fresh evidence, used OCR, and performed a new guarded Save. The fresh arm entered once, obtained a second model grounding, then checked the current image with the same OCR rule before guarded Save; the stale reference does not control its decision. Both saved exactly 329 and 517, independently parsed from the FODS, and verified neutral input releases.

| Arm | Host launcher | Task interval | Model calls | Input tokens (cached subset) | Output tokens | OCR calls |
|---|---:|---:|---:|---:|---:|---:|
| compiled, stale-reference recovery | 13.078 s | 7.952 s | 1 | 12,197 (0) | 78 | 2 |
| fresh regrounding | 13.782 s | 11.408 s | 2 | 25,779 (20,352) | 156 | 2 |

The launcher interval includes host and container start through both exits; the task interval starts after app startup and ends after independent scoring. Initial input/source preparation, stale-reference creation, image build/pull and postrun audit are excluded. No separate schema preflight was made. Cached counts are already included in input; provider cost is unknown.

The comparison is one ordered pair with a deliberately invalid compiled reference and different method behavior. Provider/cache/load effects are not controlled, and the fixed geometry and known expected values make this a constrained perception fixture. This result does not establish general efficiency, recovery reliability, a completed second-domain milestone, or MAP01 completion. Issue 57 remains open.

Run `python audit.py` with Pillow installed. It pins and verifies the retained archive, input hashes, independently parses the saved FODS, reconstructs both OCR crops from the captured PNG, validates OCR output and confidence, checks guarded execution and neutral releases, links all model calls and usage, and checks cleanup. `public.zip` retains raw runner inputs, outputs, model calls and conditions; private model session journals are hash-indexed rather than published. Source/image bytes are not fully reproduced. The legacy OCR evidence field says psm 11; recorded runner calls use psm 7 and are the relevant call trace, not an OS-level trace.
