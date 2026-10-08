# A04: A14 ROI identifiability boundary

This audit establishes whether a pixel-region comparison can be reconstructed from the retained A14 record. It is a posthoc audit of an exploratory protocol-deviation trace, not a new experiment or efficacy result.

The frozen A14 runtime event stream and reduced trace retain timestamps, a full-frame RGB SHA-256, health, and ammo. They contain no image bytes, ROI crops, or per-region measurements. The original A14 image files are not present in this retained package. Therefore region-level pixel-change counts cannot be computed reproducibly from these artifacts. ROI images found in a different MAP01 run must not be aligned to A14 timestamps.

Run `python -B audit_roi_identifiability.py` from this directory. The check verifies the pinned event-stream identity, observation schema, explicit protocol-deviation label, prior overlap-audit result, and absence of same-package image files.

The A03 overlap arithmetic remains descriptive: 7 intervals, 146 observations, 139 adjacent pairs; all 139 full-frame hashes changed, while health and ammo stayed constant in 128 pairs. This does not establish semantic threat, cover appropriateness, or any causal effect. The live Issue #59 gate remains open.

