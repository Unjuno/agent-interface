# CPU/CUDA backend diagnostic (#2479)

Research-only diagnostic for the retained X11 fresh-family split.

It trains the same small CNN separately on CPU and deterministic CUDA with the same seed, then compares classification and positive-confidence routing on the same heldout frames.

It does not change runtime policy, choose a threshold, or claim generalization. The raw frame manifests are intentionally not stored in the repository; provide the retained local `shiftout/` and `freshout/` directories beside the script.
