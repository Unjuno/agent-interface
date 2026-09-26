# Construction record — Issue #4567

Source main commit: `d823943868ff73e81fed278e9a00ca6422fdf50d`
Predecessor #4546: preserved as STOP; its formal invocation is not reused.

## Data lineage

This corrective allocation reuses the exact deterministic synthetic corpus from #4546. It contains 240 raster PNGs across 12 locally authored template families (8 train, 4 held out, 20 images/family). It is not a new data collection and provides no real-application evidence. Every PNG is checked against the frozen manifest hash.

## Corrected input path

The prior STOP arose because the v1 loader joined `images/...` against the experiment directory instead of `corpus/`. V2 centralizes resolution in `resolve_corpus_image(corpus_root, record)`, rejects any resolved path outside the frozen corpus root, and joins under `research/analysis/gpu_grounding_template_diversity_2912_v2/corpus`. `load_rows` verifies image bytes before decoding. The CPU construction suite explicitly resolves and hashes all 240 rows and includes a traversal-corruption test.

## Construction evidence

- Python bytecode compilation: recorded in `construction/01/py_compile.log`.
- CPU-only construction tests: recorded in `construction/01/cpu_unittest.log`; the full CUDA determinism test is deliberately omitted while #4205 is active.
- No optimizer updates or model training occurred during construction.
- Formal execution is not authorized until a fresh local GPU-idle/serialization check, complete GitHub MCP readback, and issue-allocation check pass.
