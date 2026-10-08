# Native GUI clutter and occlusion

A separate Tk capture collected 120 native 320x240 client frames. Each had 12 gray clutter marks; positive frames used randomized square sizes and every third positive frame had a black partial occluder. GDI bytes, receipts, and SHA-256 were retained. The same 354-parameter CNN trained for 100 CUDA epochs with an 80/40 deterministic split.

Result: 120 frames, 120 unique hashes, CUDA/RTX 3080, held-out accuracy 97.5%, false positives 0. Native GUI complexity reduced accuracy from the clean-fixture 100% to 97.5%. This is bounded local-filter evidence, not real-application transfer. Next add stronger occlusion and temporal/stale-receipt cases with unknown/yield.
