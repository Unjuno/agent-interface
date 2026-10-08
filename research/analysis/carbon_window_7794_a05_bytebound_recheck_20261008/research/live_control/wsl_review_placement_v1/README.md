# WSL retained-review storage comparison

After primary use recorded in #3501, a single resumed reply spent about 95 ms in review. This follow-up profiles the same retained completed report; no GUI, model, sensor or new action is started.

The eight-read cProfile run spent 675 ms total: 369 ms cumulative in path resolution, 180 ms in file reads, and 35 ms in receipt compaction. These categories can overlap and include profiler overhead; do not add them as independent wall-clock phases.

The unprofiled comparison copied the exact report and linked PNG to a fresh /tmp directory, and alternated location order over eight rounds. Both locations used explicit original-root mapping. Report and image hashes matched in all reads; original bytes remained unchanged. Median review time: Windows mount 88.17 ms, Linux /tmp 1.77 ms. Path depth/length, filesystem, metadata access and warm-cache effects are not separately controlled. These results do not establish cold-cache or general OS behavior, or a whole-interface speedup.

Practical next integration step: place the next owned WSL allocation's active artifacts on the Linux filesystem, retaining/copying completed evidence for review afterward. The existing explicit allocation/run-directory options already permit this; no default, safety check or input semantics need change. Verify actual end-to-end behavior there before claiming a latency improvement.

The scripts retain their exact local input/output paths for provenance; they are diagnostic scripts, not turnkey benchmarks. See source.json for the code boundary and #3501 for the input bundle. comparison.json contains every sample. No tokenizer usage, cost, model-visible arrival or human baseline was measured. The earlier source remains unchanged.
