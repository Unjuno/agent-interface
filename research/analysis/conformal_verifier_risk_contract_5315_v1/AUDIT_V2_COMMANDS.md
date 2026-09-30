# Auditor-v2 successor invocation

Run exactly once against the immutable allocation-01 raw and receipt. This command does not invoke the formal runner.

```sh
docker run --rm --network none --read-only --cpus=1 --memory=512m --pids-limit=128 \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1,dst=/src,readonly \
  --mount type=bind,src=/private/tmp/agent-interface-5315-research-20260930/research/analysis/conformal_verifier_risk_contract_5315_v1/results,dst=/out \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m --workdir /src \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B audit_v2.py --raw /out/formal-01/raw.jsonl --receipt /out/formal-01/receipt.json --out /out/formal-01/audit-02.json
```
