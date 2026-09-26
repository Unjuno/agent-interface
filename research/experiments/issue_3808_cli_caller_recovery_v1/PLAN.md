# Issue #3808 — retained-result recovery after downstream truncation

## H / T / D / C / U

**H** — When current CLI `main()` fully accepts its serialized response and exits 0, but an intermediate relay delivers only a strict prefix, a recovery-aware caller can detect failed JSON parsing, obtain the exact persisted result through read-only `attempt-status` and `review`, and keep the synthetic dispatch count at one. Producer exit 0 alone does not prove caller receipt.

**T** — Frozen base main `ddb311528e96e2a613dd660f8cb24b14f413081d`. Run one source-read-only, network-disabled OrbStack container against the public CLI entry point with a synthetic dispatch facade. Exercise (1) complete delivery control, (2) exit-0/full-acceptance plus strict-prefix relay and read-only recovery, (3) request-only unknown control, and (4) pre-existing run-directory refusal. Retain relay bytes, caller bytes, parsed states, CLI exit codes, retained report/status/review values, dispatch counts, before/after attempt snapshots, source digests, and cleanup. No GUI, input, model, provider, or network.

**D** — `PASS_CALLER_RECOVERS_AFTER_DOWNSTREAM_TRUNCATION_SCOPED` only if the producer accepts all bytes and exits 0, the relay delivers a strict prefix that the caller cannot parse, read-only status and review recover the exact retained report, files remain byte-identical, and dispatch is exactly once. The complete control parses normally; request-only status remains unknown/replay-disabled; an occupied run directory refuses before dispatch. Any false completion/replay is FAIL; setup/provenance mismatch is STOP; incomplete audit is HOLD. One formal execution, no retries.

**C** — OrbStack Docker Linux/arm64; pinned Python 3.12 slim image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--network none`, read-only root/source, separate output. Only a synthetic dispatch facade is patched; the real CLI parser, attempt persistence, `attempt-status`, and `review` paths run. No production modifications.

**U** — One deterministic CLI/caller boundary with simulated downstream truncation. Not real network/OS truncation, a live GUI/task, power-loss durability, latency/token benefit, or broad reliability. It does not close Issue #3711's wider adoption gates.

## Frozen source digests (SHA-256)

- `runtime/cli_v1/attempt.py`: `1af779f96e6519dbf7f07119e24557b3cab8c89246ed06dcf399ca2c0e03aa1d`
- `runtime/cli_v1/__main__.py`: `5731e03753dec1afdb7f4d5c035c3ba4ff5dd2c0c9eadb039ec386b3ba066122`
- `runtime/cli_v1/review.py`: `05630175233f2ad1a6ed3ecf00a316a2b7dd45bde353ea4af4c13eb1f5c4e4c1`
- `runtime/cli_v1/api.py`: `78ab68218b7555d0c589f5848970c24a226e10dbd8fd7e9ef2b88e3af7e8796e`
- `runtime/cli_v1/receipt.py`: `ae6e7932bcef1c2d2c02e952277dc4c52f16e1a392d98e8652ef45097ff44a26`
- `runner.py`: `1a6f7be7625cb908a771ef232bb2579c36f3a104ab2fc1de4d873b29c7dbcfc3`
- `audit.py`: `a783a29fc99a741cf594ca37ffe7f66db1997e9cfeeee9a18a7ca2a8535ef36b`
- Python container image: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/arm64

The runner and independent auditor are frozen by their Git blobs at the commit that adds this plan. Formal execution may start only after both scripts and this plan are committed and their SHA-256 values are posted to Issue #3808.
