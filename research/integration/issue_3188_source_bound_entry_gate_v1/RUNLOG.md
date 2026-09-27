# Run log — Issue #3188 source-bound execution

## Formal-01 — STOP before container creation

Frozen command attempted with the immutable image ID as the Docker CLI image reference. OrbStack returned `No such image`; no container was created and candidate source was not executed. No `raw.json` exists in `results/formal-01/`. This is an invocation/setup STOP, not a scientific result. The exact CLI output and disposition are retained in `results/formal-01/container.log` and `STOP.md`. No same-ID retry occurred.

## Formal-02 — exact main candidate execution

Before invocation, `python:3.12-slim` was re-inspected and resolved to the exact frozen image ID `sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9`, Linux/arm64. Candidate runner and audit hashes were rechecked against preregistration. The output path was confirmed absent. The candidate directory was mounted read-only; network was disabled; root filesystem was read-only; only the dedicated output directory was writable; the container used `--rm`.

Command:

```sh
docker --context orbstack run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  -v "$PWD/research/analysis/map01_matched_recovery_entry_gate_3008_v2:/src:ro" \
  -v "$PWD/research/integration/issue_3188_source_bound_entry_gate_v1/results/formal-02:/out:rw" \
  python:3.12-slim python /src/run.py /out
```

Observed stdout: `RAW vectors=32 controls=5`.

Raw file SHA-256: `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`.

## Candidate audit, separate container

The main-branch `audit.py` ran against the formal output mounted read-only in a fresh network-disabled container. It returned:

```text
PASS_AUDIT rows=37 vectors=32 authorize=1 current=HOLD controls=5/5
```

This is the candidate's own audit, not the independent-audit gate.

## Frozen independent audit v1 — retained failure

The pre-formal frozen verifier ran in a fresh network-disabled container. It returned `FAIL_AUDIT`, with `vector coverage/order/uniqueness mismatch` and `independent summary mismatch`. Five corruption challenges were rejected. Source inspection isolated two verifier defects: bitmask generation made the lowest-order bit vary fastest while the candidate serializes Python `itertools.product` order, and the verifier's `rows` summary counted only 32 vectors instead of 37 total vector/control rows. Its raw and output are preserved at `results/independent-02/`; formal decision is HOLD, not PASS.

## Supplemental independent audit v2 — post-outcome reconciliation

Without rerunning the candidate, a separately versioned independent verifier corrected only the two oracle defects. In a new network-disabled container, formal raw was mounted read-only, exact candidate source was mounted read-only for hash verification, audit source was mounted read-only, and only `results/independent-03/` was writable. It independently returned `PASS_INDEPENDENT_AUDIT`, zero errors, 32 vectors, one AUTHORIZE, 37 total rows, current HOLD, 5/5 controls HOLD, and five corruption controls rejected. The recomputed raw SHA-256 exactly matches formal-02.

Because this auditor was authored after observing v1's failure, it is corroboration only. It does not replace the frozen formal disposition `HOLD_FROZEN_AUDITOR_DEFECT`.

## Reproduction notes

All candidate/audit containers were local OrbStack Linux/arm64, network-disabled, and launched with `--rm`. No input/action/game/model behavior occurred. The error log from formal-01's image-ID syntax attempt is kept distinct from scientific stdout. All hashes are in `SHA256SUMS`.
