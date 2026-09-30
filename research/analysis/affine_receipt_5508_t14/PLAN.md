# Issue #5508 T14 — concurrent sink delivery admission

## H/T/D/C/U

- **H:** For a consumed receipt expecting attempt `attempt-t14` / delivery `d1`, an SQLite sink with an atomic unique delivery key serializes eight near-simultaneous identical delivery requests into one effect row plus seven identical-duplicate suppressions, allowing the exact attempt to remain confirmable. Eight concurrent distinct delivery IDs for the same attempt create eight effect rows and must remain `UNKNOWN` even when every row writes the expected semantic target.
- **T:** One deterministic two-case allocation; each case releases eight child processes from a common filesystem latch into the same SQLite sink. Case A sends the exact same `(delivery_id=d1, target=target-7, payload=payload-1)`; case B sends distinct IDs `d1` through `d8` with the same target/payload. The receipt journal and sink are separate file-backed SQLite DBs. A separate auditor reconstructs per-worker sink outcomes, row cardinality, receipt lineage, and final target. No randomization, model, GUI, network, tuning, or external service.
- **D:** PASS only if case A yields exactly one `INSERTED`, seven `IDENTICAL_DUPLICATE_SUPPRESSED`, one sink row, matching receipt lineage, and `CONFIRMED_SAME_ATTEMPT`; case B yields eight `INSERTED`, eight rows, semantic target still `target-7`, and `UNKNOWN`; independent audit matches both cases and every child exits zero. Any duplicate admission, lost insert, false confirmation, child failure, or audit mismatch is FAIL. The barrier verifies concurrent readiness and shared release, not actual overlap inside SQLite's serialized write critical section.
- **C:** A sink with native transactional idempotency is effectively what is being modeled; a distributed service may provide different uniqueness and consistency semantics. This experiment does not compare such services.
- **U:** The filesystem latch and local SQLite model concurrent arrival only at a process boundary on one host. It proves nothing about network partitions, multi-host contention, crash/power loss, external effects, or semantic truth beyond the authored target-state table.

## Frozen matrix

| Case | Eight released worker requests | Required result |
|---|---|---|
| `same_delivery_race` | all send `d1`, `target-7`, `payload-1` | 1 inserted, 7 identical suppressions, 1 row, CONFIRMED |
| `distinct_delivery_race` | worker i sends `d(i+1)`, all target/payload identical | 8 inserted, 8 rows, target matches but UNKNOWN |

No reruns or retries of the matrix. Any infrastructure problem is preserved and classified STOP; any changed allocation is separately preregistered.

## Execution freeze

Base HEAD: `ae727543f47e48bb1686e706b21ed5d9ba1cc31d`. OrbStack Docker Linux/ARM64, `--network none`. Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

Runner, independent auditor, and mutation-control hashes are posted to Issue #5508 before execution. The exact one-time run command is:

```sh
docker run --rm --network none \
  -v "$PWD/research/analysis/affine_receipt_5508_t14:/work" \
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /work/experiment.py --outdir /work/raw/formal
```

After the single allocation, the frozen auditor and mutation controls may inspect retained output without re-running the matrix.

## Lineage

T13 examined sequential sink duplicate, conflict, and ordering semantics. T14 moves only the sink admission boundary to eight child processes released from one latch. It does not repeat T5's concurrent receipt-store test or T13's sequential matrix.
