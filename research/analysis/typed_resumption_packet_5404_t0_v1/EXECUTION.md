# Execution record — Issue #5404 T0

## Preregistered allocation

- Allocation: `typed-resumption-5404-t0-orbstack-20260930-01`
- Source freeze: `2026-09-30T10:38:13Z` UTC; hashes in [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md)
- Context: OrbStack; Docker Engine 29.4.0; Linux/arm64
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Isolation: network none, read-only root/source, 1 CPU, 256 MiB, 64 pids, all capabilities dropped, no-new-privileges; only `raw/` writable.
- Formal: exactly one invocation. Auditor: one separate raw-only invocation only if formal exits 0. No retry, replacement, source tuning, or post-hoc source edit.

### Exact formal command

```sh
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges -v "$PWD/research/analysis/typed_resumption_packet_5404_t0_v1:/src:ro" -v "$PWD/research/analysis/typed_resumption_packet_5404_t0_v1/raw:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/experiment.py
```

### Exact separate audit command (only if formal exits 0)

```sh
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges -v "$PWD/research/analysis/typed_resumption_packet_5404_t0_v1:/src:ro" -v "$PWD/research/analysis/typed_resumption_packet_5404_t0_v1/raw:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/audit.py
```

## First outcome

Formal invocation: exit 0, exactly one invocation, `2026-09-30T10:39:20Z` UTC. Captured stdout:

```text
{"benign_full_replay_steps_mean": 7.0, "benign_packet_steps_mean": 2.0, "formal_invocations": 1, "opaque_unsafe_admissions": 45, "packet_invalidation_detections": 48, "packet_unsafe_admissions": 0, "policy_outcome_count": 150, "scenario_count": 50}
```

Separate raw-only audit: exit 0, `2026-09-30T10:39:27Z` UTC. Captured stdout:

```text
{"benign_full_replay_steps_mean": 7.0, "benign_packet_steps_mean": 2.0, "errors": [], "mutation_controls_rejected": [true, true, true, true], "opaque_unsafe_admissions": 45, "packet_unsafe_admissions": 0, "policy_rows": 150, "raw_sha256": "4a5cd7869d2824c293d418f968403b0b8ab65e977268982b44a2a9ebb9860b35", "scenario_rows": 50, "status": "PASS_TYPED_RESUMPTION_SCOPED"}
```

- Raw SHA-256: `4a5cd7869d2824c293d418f968403b0b8ab65e977268982b44a2a9ebb9860b35`
- Audit JSON SHA-256: `010c09ed7043567eb9cae89c4d4a107a4b02f25b831b4108e70b3fd0b3fcb741`

The pre-freeze construction smoke reported the same headline counts, but its scratch raw was discarded and is not used as formal evidence. Formal source and result were not rerun or modified. `--rm` was used without a CID file, so container IDs were not captured.
