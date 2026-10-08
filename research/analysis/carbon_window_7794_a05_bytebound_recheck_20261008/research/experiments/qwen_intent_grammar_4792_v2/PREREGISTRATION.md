# Successor #4861 — recovered exact-adapter diagnostic

This is an additive, one-shot diagnostic package. It does not alter #4792/#4803, #4856/#4858, or the trie-construction-only #4854 result. See Issue #4861 for the complete H/T/D/C/U and immutable lineage.

- Allocation: `qwen-intent-grammar-4792-recovered-20260927-02`
- Main observed at intake: `da3a8e93d426dd7af803776b51583835678f6c00`; current main when package was frozen: `f44ee126017520659bc838c6149ce17dd45a94af`.
- Branch: `research/qwen-intent-grammar-4792-recovered-v2-2`
- Path: `research/experiments/qwen_intent_grammar_4792_v2/`
- Fresh data: `make_rows(4792962, "heldout", 32)`; never reuse seed 4792961 from #4856 or the #4792 formal rows
- Model: cached Qwen2.5-0.5B-Instruct snapshot `7ae557604adf67be50417f59c2c2f167def9a775`; exact seven-file SHA-256 map is in `formal/src/FREEZE.json`
- Adapter: exact recovered bytes identified by #4792 fit.json, 2,175,168-byte weights and 701-byte config; SHA-256 values are in the freeze. The config's historical `/model` path is rewritten only in the temporary run mount to the mounted container path; the committed source artifact remains byte-exact.
- Runtime: cached image `qwen05b-action-sft:build01`, ID `sha256:63ce8205b5e0cf7daddac087d6c1bd5489d51e3af345cf923af925026bdd600c`, linux/amd64; CPU only, float32, 2 intra-op threads, 1 inter-op thread, eager attention, greedy, 48-token cap, one model load, zero fitting, no network and no retries.
- Candidate generation is state-only. Same input/prompt/adapter and greedy settings in paired free/constrained arms; trie token masking is the sole arm difference.
- Decision thresholds: full independent audit; 8/8 copied-evidence corruption controls rejected; constrained canonical candidate JSON 32/32; zero unsafe/mismatched effects; constrained exact intent >=70% and paired gain >=20 percentage points. Otherwise preserve FAIL/STOP/HOLD as observed.

## Frozen local commands (PowerShell)

Set `$root`, `$src`, `$modelhub`, `$snapshot`, `$adapter`, `$input`, and `$output` to the local package/source, Hugging Face cache, adapter copy, and fresh per-allocation directories. Never point `$output` to a nonempty directory. GitHub holds the adapter weights as six UTF-8 base64 parts because the MCP transport caps individual payloads; retrieve them losslessly, run `reassemble_adapter.py`, and require its exact size/SHA gate before any formal input generation. Read back and verify every source/artifact blob from the successor branch and verify the local Docker image ID and all model hashes against the freeze.

Construction tests (no model load or formal input generation):

```powershell
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus 1 --memory 2g --pids-limit 64 --tmpfs /tmp:rw,noexec,nosuid,size=128m -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e CUDA_VISIBLE_DEVICES= -v "${src}:/src:ro" qwen05b-action-sft:build01 -B -m unittest discover -s /src -p test_construction.py -v
```

Only after preregistration and exact GitHub readback, generate the formal input exactly once in a small offline CPU container, retaining stdout/stderr/exit and its SHA-256:

```powershell
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus 1 --memory 2g --pids-limit 64 --tmpfs /tmp:rw,noexec,nosuid,size=128m -v "${root}:/bundle:ro" -v "${input}:/out:rw" qwen05b-action-sft:build01 -B /bundle/src/prepare_input.py --out /out/DATASET.json
```

Then run exactly once with source, model, adapter and input read-only; root read-only; no GPU/network/download; and a fresh writable output mount. `$adapter` must contain the two byte-exact files from `formal/src/recovered/` at its root; do not rewrite the committed adapter config.

```powershell
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,noexec,nosuid,size=128m -e CUDA_VISIBLE_DEVICES= -e NVIDIA_VISIBLE_DEVICES=void -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e EXPERIMENT_IMAGE_ID=sha256:63ce8205b5e0cf7daddac087d6c1bd5489d51e3af345cf923af925026bdd600c -v "${root}:/bundle:ro" -v "${modelhub}:/hf:ro" -v "${input}:/input:ro" -v "${adapter}:/adapter:ro" -v "${output}:/out:rw" qwen05b-action-sft:build01 -B /bundle/src/run_pair.py --freeze /bundle/formal/src/FREEZE.json --model /hf/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775 --adapter /adapter --input /input/DATASET.json --out /out
```

Run the raw-only auditor once in a separate CPU container after the pair run, with freeze/source/model/input/raw read-only and audit output fresh/writable:

```powershell
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus 1 --memory 3g --pids-limit 64 --tmpfs /tmp:rw,noexec,nosuid,size=128m -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -v "${root}:/bundle:ro" -v "${modelhub}:/hf:ro" -v "${input}:/input:ro" -v "${output}:/evidence:ro" -v "${audit}:/audit:rw" qwen05b-action-sft:build01 -B /bundle/src/audit_pair.py --freeze /bundle/formal/src/FREEZE.json --data /input/DATASET.json --raw /evidence/RAW.jsonl --model /hf/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775 --out /audit
```

Run all eight declared corruption controls once against copies only, in an isolated CPU container (fresh `$controls` output):

```powershell
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus 1 --memory 4g --pids-limit 64 --tmpfs /tmp:rw,noexec,nosuid,size=256m -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -v "${root}:/bundle:ro" -v "${modelhub}:/hf:ro" -v "${input}:/input:ro" -v "${output}:/evidence:ro" -v "${controls}:/controls:rw" qwen05b-action-sft:build01 -B /bundle/src/run_controls.py /bundle/src/audit_pair.py /bundle/formal/src/FREEZE.json /input/DATASET.json /evidence/RAW.jsonl /hf/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775 /controls
```

A process/infra/audit failure is terminal for this allocation: preserve the first STOP/FAIL/HOLD, do not rerun or tune.

## Size policy

Commit only the small source/freeze/protocol and exact adapter needed to reproduce the diagnostic; do not commit the 988 MB base model, model cache, Docker image, or generated per-row input/raw outputs. Keep full raw outputs in the local retained bundle and publish their SHA-256, byte count, row/call counts, audit summary, terminal state and exact invocation receipts in the additive result index/PR. This keeps GitHub handoff lightweight without losing verifiability.
