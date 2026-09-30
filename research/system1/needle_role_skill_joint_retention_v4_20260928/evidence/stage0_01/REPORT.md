# v4 Stage 0 — one-shot FAIL

Result: FAIL_ZERO_UPDATE_CONSTRUCTION_GATE. This is a construction/test result, not a scientific role-LoRA result.

- Docker: 29.8.0, Linux/x86_64 daemon; pinned local image sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e (linux/amd64, Python 3.12.14).
- Isolation: --pull=never, --network none, read-only root/source, 0.25 CPU, 2 GiB, 64 PIDs, 64 MiB /tmp.
- Result: 13 tests; 12 passed, 1 failed; exit 1. No optimizer steps, no construction seed run, no formal fits, no retry.
- Failure: test_duplicate_batch_mean_loss_control used exact float equality. Singleton CE=1.4917227029800415; duplicated-row batch CE=1.491722822189331; delta=1.1920928955078125e-7. All launcher-boundary, source guard, route, split/hash and invalid-input tests passed.
- Scope: test exposes a too-strict numerical equality assertion under this pinned CPU/PyTorch execution. No evidence about LoRA quality, A-retention or B-acquisition. No hypothesis conclusion.
- Do not rerun this v4 allocation. A correction using a preregistered narrow floating tolerance requires a fresh allocation and fresh seed block.