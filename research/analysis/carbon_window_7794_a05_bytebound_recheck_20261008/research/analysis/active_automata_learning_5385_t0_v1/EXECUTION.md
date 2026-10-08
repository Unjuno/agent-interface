# Execution record — Issue #5385 T0

## Preregistered formal allocation

- Allocation: `active-automata-5385-t0-orbstack-20260930-01`
- Frozen time: `2026-09-30T10:08:07Z` UTC
- Source identities: see [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md)
- Context: OrbStack, Docker Engine `29.4.0`, `linux/arm64`
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Controls: `--network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges`; source bind read-only; only `raw/` writable.
- Formal invocation budget: exactly one. Audit: one separate raw-only invocation, only if formal exits 0. No retry/replacement/tuning.

### Exact formal command

```sh
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges -v "$PWD/research/analysis/active_automata_learning_5385_t0_v1:/src:ro" -v "$PWD/research/analysis/active_automata_learning_5385_t0_v1/raw:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/experiment.py
```

### Exact independent-audit command (conditional on formal exit 0)

```sh
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges -v "$PWD/research/analysis/active_automata_learning_5385_t0_v1:/src:ro" -v "$PWD/research/analysis/active_automata_learning_5385_t0_v1/raw:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/audit.py
```

## First outcome

Formal invocation: **exit 0**, one invocation, `2026-09-30T10:09:32Z`–`10:09:33Z` UTC.

Captured stdout:

```text
{"discovered_states": 4, "equivalence_rounds": 1, "equivalence_words": 2801, "membership_calls": 204, "raw_path": "/out/formal.jsonl", "raw_records": 2801}
```

Raw SHA-256: `2b99073cdceda44599706696d4d2f11297b653c84074763857d69b075a96d421`.

Separate raw-only audit: **exit 0**, one invocation, `2026-09-30T10:09:51Z`–`10:09:52Z` UTC.

Captured stdout:

```text
{"errors": [], "expected_bounded_words": 2801, "hypothesis_state_count": 4, "membership_calls": 204, "mutation_controls": {"budget_overrun_rejected": true, "changed_output_rejected": true, "dropped_word_rejected": true, "wrong_state_count_rejected": true}, "raw_sha256": "2b99073cdceda44599706696d4d2f11297b653c84074763857d69b075a96d421", "rows": 2801, "status": "PASS_ACTIVE_LEARNING_SCOPED"}
```

Audit JSON SHA-256: `d662092da48b99759977373394525a839de750a2e8c5c49929aed9f116574ffd`.

The pre-freeze construction smoke ran once in OrbStack and printed: 4 inferred states, one bounded-equivalence round over 2,801 words, 204 membership queries, and a raw-only auditor PASS with four mutation controls rejected. Its temporary output was not retained and it is not formal evidence; no scientific conclusion relies on it. The formal result did not rerun that smoke.
