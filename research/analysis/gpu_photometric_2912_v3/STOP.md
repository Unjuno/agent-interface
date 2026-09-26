# Formal allocation STOP — Issue #4470

Date: 2026-09-26 UTC. Allocation: `gpu-photometric-2912-deterministic-pool-4470-01`.

Exactly one formal runner invocation occurred on the local NVIDIA GeForce RTX 3080 Laptop GPU. The allocation ran from 2026-09-26 14:02:27.862 UTC to 14:02:33.441 UTC and exited 1 before the first optimizer step. The frozen source commit was `5b3096f22ee7b5b12acc3b32e41067388462cae9`; canonical freeze SHA-256 was `de2182d9578490e4e8b87213e2f7dec3ba7dec22e8a5b32ff8f462c02f40dd02`.

Failure: the actual CNN feature-map shape was `(25, 40)`, but `DeterministicAdaptiveAvgPool2d` was constructed to require `(40, 25)`. The runner raised `ValueError` in its first training forward. No `results.json`, completed step, held-out prediction, scientific metric, or augmentation comparison exists. This is an implementation/coverage failure and neither supports nor refutes the scientific hypothesis.

Preflight: 314,485,723,136 bytes free on C:, 16,167 MiB GPU memory free of 16,384 MiB, with `CUBLAS_WORKSPACE_CONFIG=:4096:8`. Exact raw execution evidence is retained in `results/formal01/`:

| File | SHA-256 |
|---|---|
| `FORMAL_METADATA.json` | `b4c53654f3c4896b41448065395fd7c9ebb4fd5600221853fdcd088441e58f46` |
| `PROCESS_EXIT.json` | `3c480c0591f476e2e50d0845f790b702ffc29b88ff93b36f45b870bb2d08c15a` |
| `runner.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runner.stderr.log` | `621b85e494eba1e364025d2ecb517049564beb3885fc3291c8dca4a6e4e37658` |

STOP is final for this allocation. Do not retry, patch in place, reinterpret as a negative experiment, or alter the frozen artifacts. A possible successor requires a new issue/allocation and additive path, a CPU assertion for the complete CNN output shape plus pooling-vs-oracle shape/value equivalence on the actual `(25, 40)` feature map, deterministic CUDA forward/backward controls, and a new single-run freeze. Keep compute bounded at 300 optimizer steps per arm and run only if that corrected construction gate passes.
