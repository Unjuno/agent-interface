# Native GUI provenance gate

The 120-frame clutter/occlusion dataset was re-read and verified against each JSON receipt.

- normal dataset: `(True, pass)`
- one tampered receipt hash: `(False, hash)`
- one frame replaced with another frame's bytes: `(False, hash)`

Canonical files were not modified. Geometry, full scanline count, raw byte length, SHA-256, and receipt label are required before a frame is accepted for training/evaluation. This is a provenance gate, not a model-performance claim.
