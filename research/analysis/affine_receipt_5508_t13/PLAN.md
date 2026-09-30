# Issue #5508 T13 — sink-side duplicate and out-of-order delivery

## H/T/D/C/U

- **H:** After an affine receipt is consumed for an expected attempt and delivery, a sink that atomically deduplicates identical delivery IDs prevents duplicate effect rows, but cannot by itself justify confirmation when a conflicting payload or a second distinct delivery ID is presented. Recovery confirms only the single exact expected delivery with the independently read semantic target; all conflicting, multiple, or unresolved lineage cases remain `UNKNOWN`.
- **T:** One deterministic, hand-authored five-case matrix using two separate file-backed SQLite databases (consumed receipt journal and effect sink) in a pinned, network-disabled Python 3.12 container: exact delivery; exact duplicate delivery ID and payload; same delivery ID with conflicting payload; a second distinct delivery ID; and out-of-order `d2` then expected `d1`. The sink uses a primary-key delivery ID and updates a simple target-state table only for newly inserted delivery rows. No randomization, model, GUI, network, clock, or external service.
- **D:** PASS only if the exact single delivery and byte-identical duplicate are each represented by exactly one sink row and can be confirmed against expected receipt lineage and target; conflicting payload is refused without overwriting the original and yields `UNKNOWN`; distinct and out-of-order delivery IDs leave multiple effect rows and yield `UNKNOWN`, even if final target state equals the expected target; the independently authored auditor reconstructs all five outcomes from raw input trace plus both databases and matches the runner. Any false confirmation, overwrite, duplicate admission, evidence mismatch, or oracle mismatch is FAIL.
- **C:** A receiver transaction that atomically binds the receipt and external effect, or a sink with a stronger authenticated idempotency/observation protocol, could avoid the conservative `UNKNOWN` outcomes. This experiment does not compare those alternatives.
- **U:** SQLite uniqueness and the authored target-state table are only a local sink simulator. No claim about real APIs, GUI effects, cross-store atomicity, host power loss, or distributed storage. The expected semantic target and event ordering are authored inputs, not independent real-world truth.

## Frozen matrix

| Case | Sink calls (ordered) | Required recovery |
|---|---|---|
| `exact_single` | `d1(target-7,payload-1)` | `CONFIRMED_SAME_ATTEMPT` |
| `exact_duplicate` | `d1(target-7,payload-1)` twice | `CONFIRMED_SAME_ATTEMPT`; second call is identical duplicate suppression; one row |
| `conflicting_payload` | `d1(target-7,payload-1)`, then `d1(target-wrong,payload-2)` | `UNKNOWN`; conflict refused, original row unchanged |
| `distinct_delivery` | `d1(target-7,payload-1)`, then `d2(target-wrong,payload-2)` | `UNKNOWN`; two rows |
| `out_of_order` | `d2(target-wrong,payload-2)`, then `d1(target-7,payload-1)` | `UNKNOWN`; two rows despite final target matching |

Frozen expected counts: `CONFIRMED_SAME_ATTEMPT=2`, `UNKNOWN=3`, `NOT_STARTED=0`. This is a single confirmatory allocation. No retries, parameter changes, or reruns of the matrix. On infrastructure failure, preserve the output and stop; any changed experiment is a separately preregistered successor.

## Execution freeze

Repository HEAD at freeze: `ae727543f47e48bb1686e706b21ed5d9ba1cc31d`.

Container: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; Docker network mode `none`; architecture observed `linux/arm64`.

Runner, auditor, and mutation-control SHA-256 values are preregistered in the Issue comment before the confirmatory run. Command:

```sh
docker run --rm --network none \
  -v "$PWD/research/analysis/affine_receipt_5508_t13:/work" \
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /work/experiment.py --outdir /work/raw/formal
```

The only allocation is the above exact five-case execution after the GitHub preregistration comment is visible. Afterwards run the independent auditor and corruption controls in the same pinned network-disabled image; these are validation of the frozen output, not a second experiment allocation.

## Lineage

T12 is retained separately as an exploratory host-side construction pilot because its runner unexpectedly executed the whole matrix before preregistration. T13 is a distinct sink-delivery discriminator; it does not repeat T12's seven crash/recovery cases. T0–T11 and T12 files remain unchanged.
