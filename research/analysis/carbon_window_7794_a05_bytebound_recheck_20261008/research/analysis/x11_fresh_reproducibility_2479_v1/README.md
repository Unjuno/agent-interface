# Fresh-family CUDA reproducibility check — #2479

This successor records one CUDA/CPU reproduction of the retained threshold
harness. The raw datasets were read from an existing workspace without
modification; their manifest hashes are retained below. No threshold or runtime
policy is promoted.

The first CUDA attempt correctly stopped because deterministic cuBLAS required
`CUBLAS_WORKSPACE_CONFIG`. A single rerun with `:4096:8` and a matched CPU run
then completed. The result is an environment/reproducibility observation, not a
new model claim.
