# Frozen commands — Issue #5315 allocation 01

Construction (executed before freeze):

```sh
python3 -m unittest -v test_construction.py
docker run --rm --network none --read-only --cpus=1 --memory=512m --pids-limit=128 \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1,dst=/src,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m --workdir /src \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B -m unittest -v test_construction
```

Before the frozen invocation, create only the empty output parent (not formal rows):

```sh
mkdir -p /private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1/results
```

One frozen formal invocation (not yet run at freeze time):

```sh
docker run --rm --network none --read-only --cpus=1 --memory=512m --pids-limit=128 \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1,dst=/src,readonly \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1/results,dst=/out \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m --workdir /src \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B run.py --out /out/formal-01
```

Independent audit runs only after the raw invocation, in a separate container process, with the frozen source read-only:

```sh
docker run --rm --network none --read-only --cpus=1 --memory=512m --pids-limit=128 \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1,dst=/src,readonly \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1/results,dst=/out \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m --workdir /src \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B audit.py --raw /out/formal-01/raw.jsonl --receipt /out/formal-01/receipt.json --out /out/formal-01/audit.json
```

The one formal command is permitted once only. Do not rerun it to repair an auditor or adjust the decision rule. A defect after formal execution is preserved and needs a new successor allocation.
