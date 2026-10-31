# WSLc Calc: matched OCR comparison with varied values

This preregistered two-arm follow-up changes the expected values from 329/517 to 641/283 while retaining the known stale 731/864 reference, fixed geometry, OCR, guards, pinned image and source snapshot. Fresh ran first (e14), compiled second (e15). Both performed one entry, independently saved exactly 641 and 283 and recorded neutral input release. Compiled yielded on the stale reference, then used fresh OCR and a new guarded Save without replaying entry.

| Route | Host launcher | Task interval | Model calls | Input tokens (cached subset) | Output tokens |
|---|---:|---:|---:|---:|---:|
| fresh regrounding | 13.140 s | 9.960 s | 2 | 25,826 (12,160) | 175 |
| compiled recovery | 9.906 s | 7.531 s | 1 | 12,209 (0) | 78 |

Both arms called Tesseract twice. Intervals and exclusions match the prior comparison: launcher from process start to both exits; task after app startup through independent scoring; source/input preparation, stale-reference creation, image build/pull and audit excluded, with no separate schema preflight. Cached input is a subset; billing is unknown.

This is one fixed-order pair on a second value pair in the same synthetic fixture, not a random task sample. Expected values are explicitly configured in the experimental cue and scorer. Provider/cache/load differences remain uncontrolled. These results do not establish a general speed or reliability improvement, broad perception, full costs, second-domain milestone completion or MAP01 completion. Issue 57 remains open.

Before running, two local unit checks were shown failing for 641/283 with the old cue/scorer, then passing after updating those expectations; they also rejected the old pair and a mixed pair. Run `python audit.py` with Pillow and the sibling original comparison packet. The audit checks the pinned archives, verifies that exactly five files differ from the original inputs and that their contents differ only by expected-value substitution after CRLF normalization, checks fresh call IDs, reconstructs OCR crops, checks OCR transcripts, independent saved FODS values, guards, input releases, model usage and cleanup. `public.zip` retains inputs and raw outputs; private protocol journals are hash-indexed. Actual Tesseract runner calls use psm 7; the older psm 11 metadata is retained, and the call trace is not an OS trace.
