# T2 execution receipt

## Construction (non-formal)

Static compilation and `git diff --check` passed. A pinned-container smoke test
checked crash TTL 3 / recovery tick 4, acquisition at exact expiry without
marker suppression, no suppression at delays 3 and 4, duplicate-marker reduction,
and stale/forged refusal. The final-source smoke output was:

```text
construction PASS: crash_ttl3_recovery_tick4, expiry_equality_admits_without_marker_suppression, delay3_and4_no_suppression, duplicate_marker_reduced_advisory, stale_and_forged_controls_fail_closed
```

## Formal allocation

One invocation, no retry. Before launch, Docker monitoring showed no active
container. Docker Engine: 29.4.0, linux/aarch64. Image:
`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
Container ID:
`d3b417119d94f4bae8b98bdc13855982e89e02f739a4842139ceac9520850af6`.
Network `none`; read-only root; 1 CPU; 256 MiB; 64 PIDs. Exit 0; start
`2026-09-30T09:39:20.426513669Z`; finish `2026-09-30T09:39:21.097744624Z`.

Exact formal command:

```bash
docker run --name ai-5346-t2-formal-20260930 --pull=never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --user 0:0 --tmpfs /tmp:rw,nosuid,nodev,size=64m -v /private/tmp/agent-interface-5315-research-20260930/research/coordination/stigmergy_5346_t2_successor:/src:ro -v /private/tmp/agent-interface-5315-research-20260930/research/coordination/stigmergy_5346_t2_successor/raw:/out:rw --workdir /src python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/simulate.py --out /out/raw.jsonl
```

Runner stdout: `{"arm_rows": 4800, "output": "/out/raw.jsonl", "scenario_count": 1600}`.

- Raw: 4,800 JSONL rows, 6,906,374 bytes; SHA-256
  `1093ab8d5750fe305e22413b470b909badea2e670a57a2d68faaabbe052ac3b4`.
- First raw-only auditor: [`audit.py`](audit.py), output retained in
  [`AUDIT_V1.json`](AUDIT_V1.json), PASS; no formal run was repeated.
- Supplemental raw-only auditor: [`audit_v2.py`](audit_v2.py), output retained
  in [`AUDIT_V2.json`](AUDIT_V2.json), PASS; specifically validates observation
  timing/fault behavior and rejects an early-observation mutation.
- Source identities captured before formal invocation are in
  [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md). T2 simulation source was not
  modified after its formal run.
