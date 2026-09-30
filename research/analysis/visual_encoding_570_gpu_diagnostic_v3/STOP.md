# Issue #4719 — Docker GPU preflight STOP

## H — hypothesis

The Issue #4719 construction lane can serve the preregistered Qwen2.5-VL 3B
Q4_K_M model from the pinned official Ollama Linux/amd64 image with verified
nonzero GPU offload on the RTX 3080 Laptop.

## T — executed first gate

At main `8140c8b04d4487b59fd4fec7629556b04e189ace`, ran exactly once:

```sh
docker run --rm --gpus all alpine:3.20 sh -c 'uname -m; if [ -e /dev/nvidia0 ]; then ls -l /dev/nvidia*; else echo GPU_DEVICE_ABSENT; fi'
```

The local Docker daemon was responsive. It returned exit 125 before container
startup:

```text
docker: Error response from daemon: failed to discover GPU vendor from CDI: no known GPU vendor found

Run 'docker run --help' for more information
```

Independent environment observations: Docker server is Linux/arm64; host is
arm64; `docker info` exposes only `io.containerd.runc.v2` and `runc`; no
`nvidia-smi` executable is available. The preregistered lane requires a
Linux/amd64 Ollama container and RTX 3080 GPU placement.

The preflight image was the already-cached
`alpine@sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc`
(`linux/arm64`). The raw-evidence audit ran in the already-cached
`python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
(`linux/arm64`). Neither image was pulled for this allocation.

## D — decision

**STOP_GPU_OFFLOAD_UNAVAILABLE** at the Docker GPU-runtime preflight. Do not
pull/start the Ollama image, issue a model request, or run the formal 6+2
allocation on this host. The failed `--gpus all` request is retained and is not
retried. This stop does not adjudicate localization quality.

## C — controls and provenance

The only container invocation was the small local Alpine GPU-device preflight;
it was not represented as the pinned Ollama construction request. No model was
substituted, no cloud/provider was contacted, and no formal screen was scored.
Raw command/environment fields are in `STOP.json`; run
`python3 -m unittest -v test_audit_stop.py` to exercise the raw-evidence audit
and its negative controls.

## U — limits

This establishes only that this current arm64 OrbStack Docker environment could
not satisfy the requested NVIDIA GPU device path. It does not prove the GPU is
unavailable on another host, that Ollama GPU offload itself is defective, or
anything about model localization capability. #570 remains open.
