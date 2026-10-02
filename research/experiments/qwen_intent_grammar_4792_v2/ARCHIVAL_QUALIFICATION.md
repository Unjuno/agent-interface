# Archival qualification: #4874 published diagnostic FAIL

## Preservation scope

This additive archive preserves the 22 already-published regular-file Git blobs from source PR [#4874](https://github.com/Unjuno/agent-interface/pull/4874), source head `2bbe9ae8521068a8f298f98386602b7015309e2d`, at their original canonical package paths. The unchanged package tree before this qualification is `43321b9a70c74bacc97ec0e9ffaef3cc5e8950a6`; its manifest reports 2,963,963 bytes. This qualification is separate from the historical source, freeze, results, audit/control summaries, and adapter transport parts.

This is identity-only preservation of published Git objects. The original blobs are referenced directly by their existing Git object IDs. Some published text records were read for interpretation, but none of the 22 original blobs was independently byte-rehashed for this preservation. The byte total comes from GitHub tree metadata. Object-identity equality is not a fresh scientific audit, recovered raw evidence, or validation of embedded SHA-256 claims. In particular, the six already-published base64 adapter parts were not decoded, assembled, loaded, or executed.

The source PR remains Draft and owner Issue [#4861](https://github.com/Unjuno/agent-interface/issues/4861) remains open. This archival action does not close either, change the original source branch, or make this code an active runtime component.

## Historical outcome remains FAIL

The unchanged [RESULT.json](formal/RESULT.json) and [FAILURE_LOG.md](formal/FAILURE_LOG.md) record `FAIL_DIAGNOSTIC_GATE_AND_CORRUPTION_CONTROL_GATE` for allocation `qwen-intent-grammar-4792-recovered-20260927-02`, fresh held-out seed 4792962.

The historical published records report 32 paired rows, 64 generation calls, one model load, and zero fits/optimizer updates. They report free exact intent 13/32 versus constrained 4/32, a paired delta of -28.125 percentage points, constrained canonical candidate JSON on 32/32, and zero unsafe/mismatched effects. The historical independent raw-only audit reports 894 checks and no errors. None of these experimental claims was independently reproduced or re-audited during this archival preservation.

The corruption-control gate remains failed: 7/8 controls were rejected. The non-rejecting `alter_constrained_text` control assigned `{"op":"save"}` to a row whose constrained text was already identical, so the attempted mutation was a no-op. This archive neither repairs that harness nor turns the historical audit summary into a passing control gate.

## Deliberately absent evidence and resources

The original [PREREGISTRATION.md](PREREGISTRATION.md) intentionally excluded the base model and generated per-row input/raw outputs from GitHub. The published package contains source, freeze, adapter/config transport, compact result/audit/control records, and historical command text. The following are only historical metadata claims in [RESULT.json](formal/RESULT.json), not artifacts supplied or verified here:

- Input: 69,415 bytes, SHA-256 `d48f40430da0ba4feb543d7682401549a1dbf343e152d2921acf31b428c56745`
- Raw output: 357,916 bytes, SHA-256 `c450980bf1f4fd6ba389e7eeaf38e07739e6c7def00dbd2e719af0eb27f8a344`
- Base model, model cache, Docker image, full local invocation receipts, and complete local evidence bundle are not included

No private/local input, raw output, model/cache, or external resource was retrieved for preservation. A recorded hash or local path cannot replace missing evidence bytes. The historical command text is retained as provenance, not an instruction or authorization to rerun the consumed allocation.

## Immutable boundaries and lineage

- Preserve the first FAIL and all predecessor STOP/FAIL results; no retry, tuning, harness repair, refit, or consumed-allocation rerun
- No new source execution, test, Docker run, model assembly/load/call, or experiment forms part of this preservation
- No verified diagnostic success, adapter promotion, runtime authority, real-GUI/task result, broad reliability/safety claim, or latency/token advantage is established
- Preserve [#4792](https://github.com/Unjuno/agent-interface/issues/4792), [#4803](https://github.com/Unjuno/agent-interface/pull/4803), [#4854](https://github.com/Unjuno/agent-interface/issues/4854), [#4855](https://github.com/Unjuno/agent-interface/pull/4855), [#4856](https://github.com/Unjuno/agent-interface/issues/4856), and [#4858](https://github.com/Unjuno/agent-interface/pull/4858) unchanged
- [#4877](https://github.com/Unjuno/agent-interface/issues/4877) is a distinct whole-candidate-ranking successor allocation; it does not replace, retry, or erase this FAIL
- The [owner outcome comment](https://github.com/Unjuno/agent-interface/issues/4861#issuecomment-5855705733) explicitly says to keep #4861 open and not merge as verified success; the [maintenance disposition](https://github.com/Unjuno/agent-interface/issues/672#issuecomment-5923336959) preserves the same limits

Ordinary publication/index checks, if later performed for this additive archive, assess publication only. They cannot establish missing raw evidence, repair the failed controls, or upgrade the original scientific disposition.
