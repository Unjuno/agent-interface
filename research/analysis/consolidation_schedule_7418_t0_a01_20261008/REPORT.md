# Issue #8406 T0 A01 — episodic memory consolidation schedule

**Result: `PASS_T0_METHOD_SCOPED`.** The candidate emitted 24 intermediate snapshots across four schedules; the independent raw-only auditor reconstructed all 24 with zero errors.

## H / T / D / C / U

**H.** For one fixed, ordered, source-bound finite ledger, changing the consolidation schedule changes intermediate derived-memory state while keeping the episode evidence and query checkpoints aligned. T0 tests schedule manipulation and audit integrity only; it does not test whether an LLM changes an answer.

**T.** Six immutable episodes were run through `episodic_only`, `per_episode`, `batch_2`, and `terminal`. Every arm records prefixes 1–6, the same full-ledger digest, prefix IDs/digest, five identical query IDs, and a fixed zero-model-call budget. The corpus contains two repeated common successes, a verified rare publish exception, two conflicting verified observations, a source-linked baseline/current history pair, and a held-out conjunction not present in evidence.

**D.** The audit matched every ledger, prefix, memory claim, provenance ID, update count, query list, and budget. The schedules applied 0, 6, 3, and 1 consolidation updates respectively. Intermediate presence of the exception differed by schedule: per-episode at prefix 3, batch at 4, terminal at 6. The contradiction was represented as `UNKNOWN` when both sources were included; the held-out conjunction was never inferred. All seven frozen hostile mutations were rejected during pre-freeze construction. Formal candidate and auditor each ran once, exit 0, with zero retries. No formal audit errors; `PASS_T0_METHOD_SCOPED`.

**C.** The episodes and deterministic consolidation transformation are authored fixtures. Different stored intermediate states do not prove different downstream task answers or a benefit from any schedule.

**U.** No model, GUI, task accuracy, token use, latency, safety, real-world exception frequency, or optimal cadence was measured. T1 requires its own allocation, fixed model/prompt/retrieval, held-out split, seeds, and independent endpoint audit. The external ARC-AGI preprint motivates schedule sensitivity but is not replicated or transferred by this T0 [Zhang et al.](https://arxiv.org/abs/2605.12978).

## Execution provenance

Concurrent, non-pooled #8406 work discovered in a later coordination check is documented in [`COORDINATION.md`](COORDINATION.md).

- Allocation: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T0-A01-20261008`
- Companion idea: #8406; distinct from #7418's representation comparison.
- Branch: `research/8406-consolidation-schedule-t0-a01-20261008`
- Current-main base and pre-run freeze parent: `bb476976d887bb0194a64a1c6ab1e7ac45d72e24`
- Frozen commit: `2fe66959c5bf76faf39bbb70659426e21f6ad6c1`
- Runtime: native macOS CPython under `sandbox-exec` network denial; no container, model, GUI, OS input, user data, or external effect. No container isolation or resource-cap claim.
- Candidate/auditor raw JSON, stdout and SHA-256 values are in `results/FORMAL_A01/` and `RUN_RECORD.json`; source hashes and commands are in `FREEZE.json`.
