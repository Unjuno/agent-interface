# Preregistration — online streamed LoRA role skill

Issue: [#3769](https://github.com/Unjuno/agent-interface/issues/3769)  
Allocation: `needle-lora-3441-online-stream-v1`  
Branch: `research/needle-lora-3441-online-stream-20260921`  
Path: `research/needle_lora_3441_online_stream_v1/`  
Base: `main` at branch creation; remote base used, no local checkout required.

## H / T / D / C / U

The immutable issue body is the controlling H/T/D/C/U record. This file binds its one formal allocation to exact source identities:

- `runner.py` Git blob: `e88dbdc21d32c6647186f6664c564faef224e781`
- `runner.py` SHA-256: `62c74d80aed3c0932967fa42bdf9eda00aea64d33a3bb7c6066ed903bb3d61d6`
- `audit.py` Git blob: `14599da23a0a1c4702b395d602e244db7af9d99c`
- `audit.py` SHA-256: `a1a7147a59845137080af113b06621c429ebbaab3a46902c4f565ed4c62436af`

Formal schedule: CPU-only deterministic PyTorch; 512 rows / 400 steps for frozen role-A base; role-B support of 16 sequential feedback rows; online role adapter gets exactly 8 AdamW steps after each feedback arrival (128 total); matched batch role adapter gets the same 128 steps only after all feedback arrives; 4096 held-out rows per role. No model/action/runtime authority, network, GUI or task input.

Decision gates (frozen before formal): both online and batch role-B held-out accuracy >=0.90; online >= batch - 0.03; role-A via base >=0.90; online feedback update p95 <=60ms; unknown role, stale epoch, wrong adapter version and missing adapter all YIELD; complete adapter state round-trip and rollback exact; base immutable. Any quality/latency miss is FAIL, route/state-integrity miss is FAIL_ROUTE_OR_SNAPSHOT_INTEGRITY. One formal invocation, no retry/tuning.

Construction-only checks before formal: runner/auditor compile from fetched GitHub source; instantiated Core/LoRA; initial state comparison exact; unknown-role and stale-epoch controls YIELD. Outcome: `CONSTRUCTION_SMOKE_PASS`. This is not formal evidence.

Execution policy: Docker availability was read-only checked; the daemon was unreachable at the Docker Desktop Linux-engine named pipe. No service start/repair, image pull, or local disk cleanup. The frozen formal source will run once in host shell on CPU if the current single-run ownership reread remains clear; report is explicitly not container evidence. Raw outcomes are retained as a compressed JSON payload with SHA-256 so per-row predictions remain auditable.
