# Local retained-result provenance verification (#2685)

Scope: validate the existing v1 fixture/result only. No model, GUI, or task experiment was run; this is not a fresh allocation.

## Environment and command

- Current-main commit checked out and verified: `9d91450fb0ef73fb34dda961965b010861c08402`.
- Docker context: `desktop-linux` (Docker Desktop); platform `linux/amd64`.
- Image: `python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`.
- Network disabled; read-only root and source mount; 0.25 CPU, 256 MiB, 32 PIDs; all capabilities dropped; no-new-privileges.
- Gate command: `python -B test_gate.py` from `research/integration/integrated_efficiency_repair_reacquisition_v2/`.
- Outcome: `PASS retained-result provenance gate`, exit 0.

## Independent raw-byte audit

A separately committed standard-library Python auditor (`audit_retained_result_independent.py`) ran in the same pinned container and independently checked fixture/result schemas and task identity, the claimed source Git blob agreement, `formal_invocation=1`, `formal_reruns=0`, exact primary comparator identity, and all eight ratio fields (seven integer measures plus `wall_ns`). It reconstructed numerator, denominator, difference, exact rational value, and the 15-decimal rounded ratio from the retained fixture; all eight matched.

Disposition: `PASS_RETAINED_RESULT_PROVENANCE_SCOPED`. The result's `fresh_allocation` is false. This validates only retained accounting/provenance and does not establish model utility, task effect, latency benefit, or new experimental execution.

Independent auditor summary:

```json
{"comparator_match":true,"decision":"PASS_RETAINED_RESULT_PROVENANCE_SCOPED","formal_invocation":1,"formal_reruns":0,"fresh_allocation":false,"ratio_count":8,"recomputed_ratio_fields":["durable_calls","input_tokens","local_observations","model_visible_images","output_tokens","planner_generations","reasoning_output_tokens","wall_ns"],"source_blob_claim_matches_result":true}
```

The exact gate stdout is retained in `LOCAL_VERIFICATION_2685.stdout.txt`; the exact independent audit stdout is retained in `LOCAL_VERIFICATION_2685.audit.stdout.txt`. The historical failed Actions run and prior result files are unchanged. This audit does not replace the original formal allocation.
