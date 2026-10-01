# Issue #6121 T0 candidate STOP — NOT EVALUATED

Allocation: `OBLIGATION-CAPACITY-6121-T0-HOST-20261001-01`  
Owner: local Windows thread `01a0b990-3d17-72f1-a908-9a2072104ce5`  
Frozen source commit: `db4b8c08cc328aad030423cb19be0c7e99416a86`  
Freeze manifest commit: `7e5eec746a31c8d4f30b45ceb196a35a1afc1ca9`  
Main at freeze: `981ba1ee20259ff36465d25aceef62fd3554a7e9`

## Outcome

The sole candidate invocation, `python candidate.py fixture.json candidate.jsonl`, exited **1** during the first synthetic obligation creation. The retained error signature is:

```text
candidate.py line 34, in create
  emit("create", tick, **{... "kind": item["kind"] ...})
TypeError: run_case.<locals>.emit() got multiple values for argument 'kind'
```

This is `STOP_CANDIDATE_RUNTIME_ERROR / NOT_EVALUATED`, not a scientific FAIL and not a hypothesis decision. No candidate JSONL was written. The independent auditor was correctly not invoked (0), and none of its five corruption controls ran (0). Candidate invocations: 1; retries: 0. The consumed allocation will not be corrected and rerun. Frozen source files are unchanged.

The tool returned a truncated traceback in its displayed output; the exact terminal exception and relevant frame above are retained, but a byte-exact full stderr artifact/hash was not available. Post-run read-only inspection confirmed both `candidate.jsonl` and `audit.json` are absent.

## Resource boundary

Host CPython 3.11.9 only. No model load, GPU/CUDA, Docker/OrbStack container, WSL workload, GUI/application effect, or network access. Docker read-only inventory had timed out before this T0; WSL Arch startup returned `Wsl/Service/CreateInstance/E_FAIL`. Nothing in the shared container inventory was changed.

Pre-invocation gate observed main unchanged at `981ba1ee20259ff36465d25aceef62fd3554a7e9`, frozen source hashes matching the manifest, and both output paths absent. The process start timestamp was not captured exactly; the invocation occurred inside the frozen 16:37–17:00 UTC local-host window and post-run inspection was at 16:38:32 UTC. The unused remainder of this host-only window is released.

No fix, replacement candidate, auditor run, or successor allocation is implied.