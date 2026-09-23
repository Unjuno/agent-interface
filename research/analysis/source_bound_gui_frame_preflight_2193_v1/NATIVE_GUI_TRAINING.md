# Native Windows GUI frame training

A Tk window was updated through 120 alternating states. After every update, Windows GDI captured the exact 320x240 client rectangle as 307,200 raw BGRA bytes. Each frame received a JSON state receipt and SHA-256. A 354-parameter CNN trained on 8x downsampled native pixels for 100 CUDA epochs with an 80/40 deterministic split.

Data: 120 frames, 120 receipts, 120 unique hashes. Device: RTX 3080 CUDA. Held-out accuracy 1.00; held-out false positives 0.

Conclusion: source-bound native-pixel-to-small-model training works on this host. The fixture is controlled and visually simple; this is not a DOOM/gameplay or general GUI-transfer result. Next add clutter/occlusion and receipt mismatch controls, then evaluate unknown/yield.
