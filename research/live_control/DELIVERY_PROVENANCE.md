# Live delivery and declared decision provenance

Actual assistant self-use on private Linux/X11 xterm, cohorts
`delivery-self-use-01` and `02`. The assistant viewed initial PNG 001, submitted
the displayed token plus Return and settle, viewed saved PNG 003, then requested
independent evaluation. Saved text equals t991019 / t991020 respectively.
Both runs release input and pass the task. This is a familiar task family with
new tokens, not held-out or matched performance evaluation.

## Contract and endpoints

Unpromoted `interactive_v16.py` keeps session_v16 and presentation_v2 and uses
`delivery_ledger_v2.py`. Each output item receives a session-local `delivery_id`.
Successful stdout flush records its start/end, UTF-8 byte count and referenced
observation in `delivery-flush.jsonl`. `delivered.jsonl` is written before stdout
and therefore still means attempted output; only the separate receipt confirms
flush. Neither means transport delivery, model viewing, acknowledgement or
semantic resolution. Broken pipe generates no successful flush receipt.

This experimental entrypoint requires submit to include:

```json
"decision_evidence": {
  "delivery_id": "delivery:2",
  "observation_sequence": 1,
  "producer": "assistant"
}
```

The declared producer can be assistant, scripted or human. A reference must name
a successfully flushed item carrying that observation (directly or in a terminal
review receipt), and must match expected_sequence. This proves only a consistent
caller declaration. It grants no authority and does not bypass the executor's
current sequence, lease or input checks. Evidence can precede a rejected program;
it is not acceptance. The old ready schema does not yet advertise this additional
entrypoint field; this document specifies it pending schema integration.

## Retained failure and verification

Version 1 (`interactive_v15.py`, `delivery_ledger.py`) reused delivery_id for both
the referenced source and the evidence record's own output ID. Output decoration
overwrote the source field; the raw journal and command retained the correct value.
Cohort 01 remains frozen as a provenance failure despite successful typing.
Version 2 uses `source_delivery_id` for the reference and retains both IDs in
cohort 02. No historical files were corrected.

`audit_delivery.py` verifies 12 reconstructed frames, both source manifests,
saved text, release, 30 matching output/flush IDs and encoded byte counts. It
reproduces the v1 collision and verifies v2, rejects unflushed and wrong-sequence
references, and checks source item immutability. Its first run used an incorrect
saved filename (`typed.txt`); inspection located `submitted.txt` and the corrected
audit passed. This was an audit-path error, not a new execution failure.

| Metric | Cohort 01 | Cohort 02 |
|---|---:|---:|
| Local accepted program | 647.260 ms | 504.793 ms |
| Stdout flush median / max | 0.078 / 0.205 ms | 0.071 / 0.103 ms |
| Additional receipt file | 11,739 bytes | 11,758 bytes |

These sequential runs are not an A/B speedup. An isolated 1,000-iteration small
synthetic bookkeeping probe measured median 7.071 microseconds (max 190.446),
excluding filesystem, stdout, lock contention, full observation copying and
projection. It is not total runtime instrumentation overhead. Actual model tokens,
delivery completion and image perception endpoints remain unavailable here.

The research ledger stores references without eviction, holds the emitter lock
through output and writes receipts synchronously. Production memory bounds,
concurrent admission/output behavior, durable failure handling and stall overhead
are not qualified. Full key/release action lineage is still absent. Next make
provenance fields discoverable and measure matched tracing on/off costs before
adopting this entrypoint or broadening background execution.
