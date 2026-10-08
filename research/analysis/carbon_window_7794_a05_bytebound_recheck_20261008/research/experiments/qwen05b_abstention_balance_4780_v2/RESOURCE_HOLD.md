# Formal-slot ownership hold — Issue #5014

Observed 2026-09-28 04:49 UTC (host nvidia-smi clock; local timezone Asia/Tokyo).

## Frozen gates already passed

- CPU-only pinned-image protocol/schema tests: 8/8.
- Exact frozen CPU preflight-only command: PREFLIGHT_OK; formal fit counter is 0; no model load or GPU invocation.
- The preregistered freeze, 14 source-file SHA-256 entries, formal input, model weights and pinned image match the recorded local values.
- The formal invocation has not started. Do not interpret this as a model result.

## Resource observations

- Host: NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB; nvidia-smi reported 0 MiB allocated and 0% utilization at observation time.
- Docker context: desktop-linux. `agent-interface-570-r3-ollama` is running `/bin/ollama serve` and has HostConfig DeviceRequests Count=-1 (all GPUs). It was not modified, stopped, or entered.
- `cranky_panini` is a separate running Xvfb/xwininfo task container with no GPU request. It was not modified, stopped, or entered.
- GitHub coordination indicates a retained GPU claimant on #4917 and unresolved resource ownership connected to #4719/#4871; transient zero GPU utilization does not release those reservations.

## Disposition

HOLD_RESOURCE_OWNERSHIP. Do not launch the frozen four-CPU GPU command until the existing GPU and Docker/CPU owners explicitly release their leases and a fresh inventory confirms the slot. Preserve the exact frozen run command and allocation; this is not a retry or a new allocation. Once ownership is released, recheck all gates and output-path absence immediately before the sole formal invocation.