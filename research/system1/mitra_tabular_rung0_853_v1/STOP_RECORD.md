# Issue #853 Rung 0 formal allocation stop record

Allocation: `mitra-cpu-rung0-853-local-20260927-01`  
Branch: `research/mitra853-rung0-local-20260927`  
Freeze: [FREEZE.json](FREEZE.json)  
Protocol: [PROTOCOL.md](PROTOCOL.md)

## Disposition

`STOP_CPU_CHECKPOINT_READ_COST_INCOMPATIBLE` — the single preregistered formal invocation was stopped before all 1,024 warm queries completed. No p50/p95/p99, full raw probability output, or independent result audit exists. This is not a completed p95 decision and is not a model-quality result.

## Direct observations

- Local Docker image: `mitra-rung0-853:local-20260927`, ID `sha256:4f836031f761d6c098cc72d699288826c3f8f84a46f4fb83160df51dc1c42516`.
- Runner container started `2026-09-27T04:06:03.025189123Z`, ended `2026-09-27T04:38:42.847495883Z`; Docker state is exited, exit code 137, `OOMKilled=false`.
- Container config: `--network none`, read-only rootfs, one CPU, 4 GiB memory, 128 pids; /src and /model were read-only bind mounts. Docker inspect retained the model, source, and output mount identities.
- Predictor fit artifacts existed in container-local `/tmp/mitra-predictor`, including `models/Mitra/model.pt` at 302,822,483 bytes; predictor directory size was 289 MiB.
- Runner process was CPU-saturated (~100%) at ~1.1–1.3 GiB resident memory.
- Two separate 20-second read-counter windows each showed `/proc/1/io:rchar` increasing by exactly 302,872,169 bytes. This is approximately one full checkpoint-sized read per window, consistent with an extremely expensive serialized prediction path. The runner performs the 1,024 query calls sequentially; this repeated checkpoint-scale I/O made completing the frozen high-cadence run operationally incompatible, so the one invocation was stopped. The I/O counter is process-wide and does not itself prove a one-to-one query count; no exact per-query latency is claimed.
- Docker emitted 216 lines of the same PyTorch warning: `pin_memory argument is set as true but no accelerator is found`. This warning did not stop the Python process.
- The PowerShell orchestration wrapper separately terminated on native stderr handling before collecting final metadata. The container remained live and was inspected directly; no replacement runner was launched.
- RTX 3080 Laptop GPU remained unused: pre-run snapshot SHA-256 `8a474a408b4d8c10fee36ca990cc0435f6d25716f90ba076de569f4d854032f7`, reported 0 MiB used; post-stop local query also reported 0 MiB used and 0% utilization. This is the preregistered CPU rung, not a GPU test.

## Integrity and scope

The frozen model/source/fixture identities were checked before launch. All 12 source and fixture files were committed on the additive branch and read back through GitHub MCP with exact content equality before launch. The container was not restarted. The uncompleted formal allocation must not be rerun under the same allocation ID.

This stop supports only the limited conclusion that this frozen AutoGluon/Mitra CPU path exhibited repeated checkpoint-sized process reads at a cadence incompatible with the intended high-frequency use. It does not establish the full 1,024-row p95, prediction quality, GPU behavior, fine-tuning efficacy, GUI benefit, or product/runtime authority. Any GPU investigation must be a separately frozen successor after collision checking; it must preserve the old stop record unchanged.
