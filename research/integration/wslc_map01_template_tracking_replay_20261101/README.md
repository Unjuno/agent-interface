# Offline replay: naive local template tracking after model delay

This exploratory, post-hoc replay reads the immutable dt02 packet from `wslc_map01_bounded_model_reground_20261101/public.zip` (SHA-256 `85d3fb9128e3f2b5f43e421e910db8fb392a700f84d0b7c5be0df3c51e61ca6b`). No new allocation, input or model call is performed. The saved fourth and fifth model images are compared; the fourth model selected `(654,548)` and the fifth selected `(610,536)`. The associated same-state simulator screen matches each X11 game-window crop pixel-for-pixel, and each model point lies within the corresponding sampled Zombieman rectangle. Those labels are an evaluator, not available to the tracker.

For each square template size, an exhaustive 2-pixel grid examines 4,941 positions within ±80 horizontal and ±60 vertical pixels in the fifth image, ranked by mean absolute RGB difference. This parameter sweep was chosen after inspecting the packet and is not preregistered.

| Template | Lowest-difference candidate | Difference | Inside fifth sampled enemy box? |
|---|---|---:|---|
| 8×8 | `(720,496)` | 3.646 | no |
| 16×16 | `(716,500)` | 5.344 | no |
| 24×24 | `(712,502)` | 7.550 | no |
| 32×32 | `(704,502)` | 11.023 | no |

All four best matches fall outside the sampled enemy box despite low pixel difference. The existing 40-pixel horizontal aim gate would also reject these specific candidates; this replay does not demonstrate an unsafe dispatched action. It shows that a low template score alone is insufficient evidence of target identity, and that the naive tracker cannot replace the model or freshness/review gates on this example. It does not estimate a failure rate, compare latency fairly, establish semantic identity, or complete MAP01. Further tests need negative and positive examples, ambiguity checks and an independent effect oracle.

Run `python audit.py` without `-O` (Pillow required) from this directory. It checks the original packet and member hashes, model outputs, exact paired-screen pixel equality, labels and all 4,941 candidate scores per size. The original live record is not modified.
