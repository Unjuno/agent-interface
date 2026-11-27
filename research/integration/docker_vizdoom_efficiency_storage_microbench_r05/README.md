# R05 Docker evidence-storage microbenchmark

Ten repetitions each wrote the same 19 compiled-adapter receipt payloads
extracted from R04 pair 19 into fresh output locations on the same Docker
Desktop bind mount. Method order rotated each repetition. The pinned
Linux/amd64 container ran without network access and with a read-only root;
only the output mount was writable. No GUI, input, recovery or task-effect
operation was performed.

| Storage layout | Repetitions | Median total | Median serialization | Median write/flush | Bytes per repetition |
|---|---:|---:|---:|---:|---:|
| Pretty JSON, one file per receipt | 10 | 31.165 ms | 0.609 ms | 30.353 ms | 15,885 |
| Compact JSON, one file per receipt | 10 | 31.340 ms | 0.319 ms | 30.830 ms | 11,318 |
| Compact JSONL, one append file with flush per record | 10 | 6.343 ms | 0.314 ms | 4.651 ms | 12,834 |

The JSONL layout was 4.91 times faster by median write-path time in this
isolated microbenchmark. Compact JSON reduced file size but not median elapsed
time. Serialization took less than 1 ms; file writes dominated this test.

This is a storage-layout lead, not a production computer-control speed result.
A flush does not guarantee durable media. JSONL also changes record indexing
and how a torn final write is detected. Before changing runtime storage, verify
`effect_ref` lookup compatibility, event ordering, partial-write detection,
replay denial, and existing readback consumers. Do not pool this result with
the R03/R04 live MAP01 route timings.

The runner, structured conditions, 19 source payloads, 30 raw method
directories, exact per-repetition timings, invocation receipt and hashes are
retained in the task-local packet
`private-packets/docker_vizdoom_efficiency_storage_microbench_20261028_r05/`.
