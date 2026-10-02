# Construction report — Issue #6354 conflict-probe contract A02

## H / T / D / C / U

- **H:** A valid role-conflict probe must use a feature vector actually present under both roles and yield distinct labels under the frozen rules: A=0 and B=`features[0]`=1.
- **T:** Read the byte-preserved allocation-01 dataset, canonically verify its frozen dataset digest, select one deterministic shared positive-first-bit vector per seed, emit a probe-only raw packet, then run a separate standard-library auditor. One candidate invocation, one auditor invocation, zero retries. No training or GPU code is invoked.
- **D:** Host construction tests passed 8/8. Candidate exited 0 and emitted three probes with labels 0/1 and overlap counts 104/102/105. The separate auditor exited 0: `PASS_PROBE_CONTRACT_SCOPED`, 3 seeds, 0 errors. Raw SHA-256 `17ef7a6e53ae51014d91164af8e343d92f3354f17bebdee72fcfa262754e63d1`; audit SHA-256 `1b1cc271f5aab159f7ddad799aadc4036e68083585382c7589369e766663da36`.
- **C:** Windows host CPython 3.11.9; finite synthetic binary feature vectors and the already-frozen #6354 source dataset. The host run checks only construction/data-contract behavior. WSLc was not invoked because this task has no assigned CPU/container interval in #5085. No Docker Desktop or Podman was used.
- **U:** No CUDA, optimizer update, model fit, online adaptation, forgetting, GUI, task effect, latency, or product result. This does not repair or replace allocation-01, does not authorize its formal candidate, and does not establish role-conditioned LoRA quality.

## Exact commands and outcomes

From repository root, using the candidate and auditor as separate host processes:

```powershell
python -m unittest discover -v -s research/analysis/needle_role_conflict_probe_6354_a02 -p 'test_*.py'
python research/analysis/needle_role_conflict_probe_6354_a02/candidate.py --dataset research/system1/needle_role_context_online_lora_6321_v1_20261002/construction-01/dataset.json --out research/analysis/needle_role_conflict_probe_6354_a02/construction_host_01/raw.json
python research/analysis/needle_role_conflict_probe_6354_a02/audit.py --dataset research/system1/needle_role_context_online_lora_6321_v1_20261002/construction-01/dataset.json --raw research/analysis/needle_role_conflict_probe_6354_a02/construction_host_01/raw.json --out research/analysis/needle_role_conflict_probe_6354_a02/construction_host_01/audit.json
```

The source dataset's canonical JSON digest is `5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685`. Canonical serialization is intentional: the original freeze records canonical JSON bytes, while a Windows checkout adds a line-ending byte to the physical file. The old dataset, freeze, and allocation result were not edited.

## Next gate

The host result is a construction diagnostic only. Before treating the packet as container-validated, obtain an explicit CPU-only WSLc lane assignment, then run the frozen tests/candidate/auditor in digest-pinned, network-disabled WSLc containers. Any future LoRA candidate is a distinct fresh allocation requiring a new source/data freeze and an exact GPU assignment; do not reuse allocation-01's expired request.
