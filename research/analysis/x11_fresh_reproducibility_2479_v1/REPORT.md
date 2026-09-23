# Report

H: the earlier fresh-family discrepancy is caused by an unrecorded execution
state rather than a justified threshold change.

T: run the fixed seed 2417 / 140-step harness on CUDA and CPU with the same
manifests. The initial CUDA attempt must stop if deterministic cuBLAS is not
configured; then one configured CUDA rerun and one CPU comparison are retained.

D: 80 held-out rows, CUDA and CPU routing counts, torch/CUDA/GPU metadata, and
SHA-256 hashes for the harness and both manifests.

C: The configured runs agree on accuracy and routing at thresholds 0.50 and
0.70, but differ at 0.60 (CUDA accept 15 versus CPU accept 28). Therefore this
does not establish cross-device reproducibility of confidence thresholds.

U: the cause of the threshold-0.60 CUDA/CPU confidence divergence remains
unknown; no threshold promotion, fresh-family generalization, or production
policy claim is made.
