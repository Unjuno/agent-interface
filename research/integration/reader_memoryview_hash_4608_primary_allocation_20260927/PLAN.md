# Plan — Issue #4608 / allocation `needle-online-snapshot-cadence-4451-localpy3135-v2`

## H — hypothesis

On this pinned local Linux/amd64 CPython 3.13.5 runtime, changing only the two SHA-256 inputs from copied `bytes` slices to `memoryview` slices preserves every reader result/refusal and lowers Python-traced peak temporary allocation for large consumed prefixes, within the predeclared wall/CPU guardrails.

## T — treatment

Preserve #4451 and its unspent v1 allocation. This successor uses additive branch `research/reader-memoryview-hash-4451-localpy3135-v2-20260927` and path `research/integration/reader_memoryview_hash_4451_v2/`. Intake main is `3842e8921bd587af6ce9c13664d087b377366747`; current-main `research/integration/event_inbox_reader_v1/reader.py` is still exact Git blob `3b4ac9af076bdc5dee94e09cbab22b17bc45173a`. The frozen predecessor candidate is blob `d33db53f88cb1e818c7964112aee6994ab4d7418`. No shared reader is changed.

Formal corpus: deterministic 1,048,576 bytes, exactly 4,096 complete 256-byte JSONL records. Cursors: records 0, 2,048, 4,064, 4,096; max 32 records per call. Run BASELINE and MEMORYVIEW in rotated pair order, three fresh child processes per arm/cursor: 24 resource workers. Two additional untimed contract workers test pagination/repeat, incomplete tail, malformed/gapped/duplicate-key records, changed prefix, wrong stream, and byte bound.

Each resource child loads/imports before timing, then brackets exactly one `read_pending` call with `tracemalloc`, `perf_counter_ns`, and `process_time_ns`. The container runner fsyncs a worker-start record before waiting, a worker-completion record after exit/timeout, and each returned row to JSONL. The one-shot timeout construction test passed: a real child timeout survived as paired journal records and a typed STOP.

Construction (excluded from formal): a disjoint 64-record corpus, 6 resource rows + 2 contract workers; independent audit; ten effective copied-evidence corruption controls; and the injected-timeout STOP control. Earlier nonformal control-harness attempts exposed a missing bundle copy and a missing return in the test mutator. The first invocation after enabling runtime freeze verification also STOPped before any worker because only the source subdirectory, not its parent FREEZE files, was mounted. These are retained preformal harness/environment outcomes; none touched a formal row.

## D — decision

PASS only if all 24 resource rows and both contract workers complete; independent output reconstruction, source/input hashes, paired receipts/cursors/refusals, durable JSONL/journal parity and all contract semantics pass; all ten corruption controls reject for recorded audit errors; at cursors 2,048 and 4,064 every candidate peak is below its matched baseline and median candidate/baseline peak ratio is <=0.75; and median wall and CPU ratios are each <=1.20. Report cursor 0/end without requiring benefit.

Any receipt/refusal mismatch is FAIL. Exact correctness with memory/timing gate miss is HOLD_MEMORYVIEW_TRADEOFF. Missing/ambiguous process, source, journal, raw, or control evidence is STOP/HOLD. One formal invocation only; no retry, replacement, exclusion, or post-result tuning.

## C — controls and alternatives

Only hash-buffer representation differs between baseline and candidate reader. Keep full-file read, prefix verification, newline count, JSON parsing, bounds, cursor semantics, and authority-neutral receipts fixed. Run locally using the exact already-cached image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` (Linux/amd64 CPython 3.13.5), with the complete bundle mounted `/study:ro`, output separately writable, `--pull=never --network none --read-only`, 1 CPU, 2 GiB, 64 PIDs. No install, user data, model/provider, GUI, input, or workflow runner.

## U — limits

Synthetic fixed-width trusted JSONL; one local CPython/OpenSSL build; three technical repetitions. The full-file bytes snapshot remains allocated; newline counting still slices bytes. `tracemalloc` excludes native/OpenSSL memory. No disk-I/O/RSS/concurrent-producer, cross-platform, live task, end-to-end, or production claim.
