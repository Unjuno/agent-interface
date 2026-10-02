# WSL runtime

Use Microsoft’s installed `wslc.exe`, not a new Podman or Docker setup. Read-only inspection at preparation found WSLc 3.0.1.0, the exact linux/amd64 PyTorch repo digest from FREEZE.json already cached, and zero WSLc containers. No image pull, build, start, CUDA call, or GPU workload has occurred for this allocation.

WSLc advertises `--network`, `--cpus`, `--memory`, `--gpus`, `--mount`, `--tmpfs`, and `--pull` controls. Its current `run --help` does not expose read-only rootfs or PID-limit flags. Source and output mounts are explicitly separated; source is requested read-only. The candidate has no network and no child-process needs. Do not infer kernel enforcement from configured flags. Capture applicable cgroup/swap evidence and disclose unavailable controls.

WSL and WSLc share this Windows host’s RTX 3080 with other runtimes. A no-process or idle-device snapshot is not a lease. Do not launch until the coordinator has explicitly assigned this exact allocation and time window.
