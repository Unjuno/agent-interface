# Execution record and runbook

Allocation 02 is distinct from allocation 01, whose internal-network construction STOP is retained on Issue #3204. This allocation uses a shared-volume file RPC: the inference container has `--network none`; a host process accepts only requests produced in the exchange mount and forwards them only to loopback Ollama. No model request has yet been made.

## Construction (mock only)

From this directory, after `FREEZE.json` is finalized:

```sh
python3 launcher.py --construction
```

This exercises the pinned container, PNG generation, exact 12-cell matrix, bounded nine-request RPC protocol, and artifact writes. The mock bridge never contacts Ollama. Its output is under `construction/` and is not formal evidence.

## Formal one-shot

The preregistration and source hashes are committed and recorded on Issue #3204 before this command. Confirm no concurrent Issue #3204 allocation has claimed `issue3204-model-facing-recovery-orbstack-02`, verify the frozen Ollama digest, and ensure `output/` and `exchange/` are empty. Then run exactly once:

```sh
python3 launcher.py
```

No retries are allowed. The host bridge enforces nine calls maximum, verifies image/model identity, and writes raw Ollama responses to `exchange/`. Container outputs and bridge receipts are retained verbatim. The formal container has read-only root/source, no network, bounded resources, and no action interface.

## Independent audit

After preserving the completed formal output and RPC receipts, stage `RESULT.json`, `BRIDGE_SUMMARY.json`, `FREEZE.json`, `manifest.json`, and `output/images/` under a fresh audit directory, with `audit.py` also mounted there. Run the independent auditor in the same pinned image with `--network none`; only this fresh directory is writable. `audit.py` does not import the runner or policy implementation. Its gate is scoped to this 12-cell synthetic status task; it is not an application-effect claim.

```sh
python3 -c 'from pathlib import Path; import shutil; s=Path("."); d=Path("audit"); (d/"output").mkdir(parents=True, exist_ok=False); [shutil.copy2(s/n,d/n) for n in ("audit.py","FREEZE.json","manifest.json")]; shutil.copy2(s/"output/RESULT.json",d/"RESULT.json"); shutil.copytree(s/"output/images",d/"output/images"); shutil.copy2(s/"exchange/BRIDGE_SUMMARY.json",d/"BRIDGE_SUMMARY.json"); shutil.copytree(s/"exchange",d/"rpc",ignore=shutil.ignore_patterns("BRIDGE_SUMMARY.json","DONE"))'
docker run --rm --pull=never --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --pids-limit 32 --memory 512m --cpus 1 --cap-drop ALL --security-opt no-new-privileges -v "$PWD/audit:/audit:rw" issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51 python /audit/audit.py
```

## Preflight STOP retained

Allocation 01 used the same pinned image and an internal-only Docker network. A read-only GET to `host.docker.internal:11434/api/tags` failed with `OSError [Errno 101] Network is unreachable`, before any model/task call. That STOP was posted on Issue #3204; allocation 02 changes only the transport architecture and remains a separately frozen successor experiment.
