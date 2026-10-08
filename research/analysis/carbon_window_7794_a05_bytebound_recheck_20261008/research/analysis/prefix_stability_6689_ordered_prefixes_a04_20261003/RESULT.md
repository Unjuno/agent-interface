# First formal result — #6809 A04 ordered prefixes

**Disposition: `PASS_METHOD_SCOPED`.** The frozen finite candidate and independent raw-only auditor each ran once in separate WSLc 3.0.1.0 containers; both exited 0. No retry occurred.

- 24 distinct traces: four two-obligation outcome combinations × six event orders.
- 96 source-derived prefixes: initial state plus each of three event applications for every trace.
- Independent reconstruction: 96/96 rows checked, zero audit errors.
- Mutation controls: 6/6 rejected (missing prefix, erased obligation, premature negative, premature positive, rewritten event order, and metric/count mixing).
- Exclusive dispositions: 66 `UNRESOLVED`, 24 `FINAL_FAIL`, 6 `FINAL_PASS`; the separately derived prefix metrics report 30 stable and 66 unresolved prefixes.
- Candidate JSONL SHA-256: `e7fef9bd44be327f4eb2b518be50f78df08d1fa304fda101c962285fea208c6f`.
- Independent audit JSON SHA-256: `0cc426b159160210faad498ea9e52208bc27f76b50dcaeb3d74a8d561f9b6416`.
- Frozen input SHA-256: `d2a371e7c0cd5d9dd427bca88c32fb0abdede445a9e57cdf0fcaeff3f3de84b3`.

The scoped result demonstrates that this authored finite method preserves pending mandatory obligations in every enumerated ordered prefix, does not wait for an unrelated optional source before a complete mandatory negative, and waits for the generation seal before a positive finalization. It does not revise the prior #6689/#6812 evidence or establish live-verifier semantics.

WSLc emitted the same warning on both invocations:

```text
wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
```

The run requested `--memory 512M`; effective memory/swap enforcement and OOM prevention are not established. There is no Docker comparison, native-WSL comparison, performance or memory-benefit claim. Full commands, timestamps, output hashes, and raw invocation receipts are in `RUN.json` and `formal/`.
