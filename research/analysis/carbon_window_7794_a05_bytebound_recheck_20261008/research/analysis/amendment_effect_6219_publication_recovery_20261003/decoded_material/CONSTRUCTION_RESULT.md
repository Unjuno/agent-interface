# Construction container record

- Local WSLc: 3.0.1.0; Linux kernel 6.18.40.1-1.
- Base main for the finalized package: `460f09c465a2ff0347917bc2a2805f78bcb5cdab`.
- Image reference: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (locally cached before run; `--pull never`).
- Command: `wslc.exe run --rm --pull never --network none --cpus 1 --memory 1G --mount type=bind,source=<this-package>,target=/src,readonly --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B -m unittest -v test_method.py`.
- Exit: 0; 3 tests passed.
- Runtime warning, preserved verbatim: `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.`
- The invocation used `--rm`; WSLc did not return a retained container ID/inspect record. Do not claim effective memory or swap enforcement. No GPU, CUDA, model, network, GUI, or user input.
- These are construction tests over the separate inline fixture. No formal fixture/oracle run, candidate output, or independent formal audit occurred in this step.
