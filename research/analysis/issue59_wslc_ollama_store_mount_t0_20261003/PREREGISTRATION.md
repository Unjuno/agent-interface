# Issue #59 WSLc read-only model-store mount boundary — allocation A01

## Status and scope

This is a bounded setup-boundary test for the model-route HOLD recorded on Issue #59. It does not consume, replace, or release the separate live-game/GPU allocation. It will not start Ollama, load a model, make an inference request, initialize CUDA, run a game, or emit GUI input.

## H / T / D / C / U

**H.** A WSLc container using an already cached Python image can mount the existing Windows Ollama model store read-only with networking disabled and can observe the three frozen Qwen model manifests plus every declared blob path and byte size. Failure of the mount, read-only attestation, coverage, or byte-size checks leaves the WSLc model-store boundary unverified.

**T.** Freeze the source package, expected manifest metadata, image digest, WSLc command, and read-only model-store path. Run one candidate container with `--pull never --network none`, one requested CPU and memory limit, the selected model store mounted `:ro`, source mounted read-only, and output mounted separately. Candidate reads each manifest and stats its referenced blobs; it does not read/hash large blob contents. Run one independent raw-only auditor in a separate container only after candidate exit 0. The auditor receives only the frozen fixture and candidate raw output, not candidate source or the model store. Run four predeclared construction mutations before freeze: writable mount, altered manifest hash, omitted model, and altered blob size.

**D.** `PASS_MOUNT_BOUNDARY_SCOPED` requires (1) exactly one `/models` mount record explicitly containing `ro` and not `rw`; (2) exact presence of the three frozen model manifests; (3) manifest SHA-256 and descriptor sets match the host-frozen fixture; (4) every referenced blob is a regular non-symlink file with declared byte size; (5) candidate and independent audit exit 0 with zero audit errors; and (6) every mutation is rejected. Any missing or mismatched evidence is retained as STOP/FAIL without retry. This does not show that Ollama can load from the store or that a WSLc container can reach an Ollama service.

**C.** WSLc 3.0.1 on this Windows host, cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, existing Windows Ollama store, bind-mount behavior, and the selected manifest set. `--memory 512M` is a requested setting only; WSLc has previously reported that effective cgroup/swap enforcement is unavailable.

**U.** This test establishes only read-only mount and metadata visibility. It does not start or configure the WSL Ollama daemon, make its host-local service reachable, verify model compatibility, load model weights, use GPU, evaluate voice/control behavior, or satisfy Issue #59's live threat-control exit condition.

## Execution boundary

No image pull, package installation, network connection, model start/load, blob-content hashing, GPU use, or modification to the Ollama store is permitted by this test. Use separate candidate and audit output directories. Preserve raw first outcomes and do not rerun a failed invocation.
