# Tiny CNN local GPU training

PyTorch 2.5.1+cu121 loaded the NVIDIA GeForce RTX 3080 Laptop GPU. A 354-parameter CNN was trained for 80 Adam epochs on the 240-frame Docker fixture with a deterministic 192/48 split.

Result: device `cuda`; held-out test accuracy 1.00; test false positives 0.

This validates actual CUDA training for local iteration only. The fixture is intentionally separable and does not support a GUI/gameplay claim. Next use the same small CNN on a less separable X11/container fixture with receipt integrity and unknown/yield gates.
