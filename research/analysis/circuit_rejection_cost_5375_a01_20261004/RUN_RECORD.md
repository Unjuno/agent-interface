# Formal run record — A01

Allocation: `CIRCUIT-REJECTION-COST-5375-A01-20261004-01`  
Main freeze: `13bab54ea6d91978247ecc1b70e5060db752367a`  
Runtime: WSLc 3.0.1.0; `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; Python 3.12.14; pull never; network none; CPU 1. Source bind was read-only; output bind was separate.

## Candidate

Pre-run `wslc container list` showed no running containers. One candidate invocation:

```text
wslc run --rm --name cir-rej-a01-candidate --pull never --network none --cpus 1 --mount type=bind,source=<experiment-a09>,target=/src,readonly --mount type=bind,source=<experiment-a09-output>,target=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python candidate.py
```

Exit 0, reported 480 rows. `raw.jsonl` is 147,085 bytes, SHA-256 `CBFE518EBC72D9F2FA74A7722B0D66924AF1EF5EEB1660CBE5929346E3B05FB8`. First row already contradicts the frozen capacity invariant: total cost 32 under capacity 20, with safety service 0. This is an observed candidate/method failure; no result gate is evaluated from it.

## Independent auditor STOP

Pre-run `wslc container list` again showed no running containers. One auditor invocation used a read-only mount for `/out`:

```text
wslc run --rm --name cir-rej-a01-auditor --pull never --network none --cpus 1 --mount type=bind,source=<experiment-a09>,target=/src,readonly --mount type=bind,source=<experiment-a09-output>,target=/out,readonly --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python auditor.py
```

It read the raw stream, then exited 1 with `OSError: [Errno 30] Read-only file system: '/out/audit.json'` when it attempted to persist its audit. No audit JSON was written. Classification: `STOP_AUDIT_OUTPUT_READ_ONLY`, not an independent audit verdict. No retries, replacement, or rerun. Candidate raw and STOP remain preserved. No WSLc cgroup/swap warning appeared in the captured command outputs; no memory limit is inferred from requested flags.

## Scope / next boundary

The first candidate row's over-capacity total is enough to reject the present candidate implementation as violating its own accounting model; the scientific H is unevaluated. Preserve this as a construction/formal-attempt failure. Any future allocation must use a new ID, corrected explicit queue/resource semantics, a separately writable audit-output destination, preregistered construction tests and fresh source hashes. It must not replay this consumed candidate allocation or rewrite this record. This synthetic attempt establishes nothing about Agent Interface production rejection cost, safety, latency, resilience or product behavior.

