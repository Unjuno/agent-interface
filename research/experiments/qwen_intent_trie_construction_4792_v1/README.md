# Qwen intent trie construction — Issue #4854

Construction-only CPU Docker probe of static canonical JSON trie decoding for the #4792 compact intent idea. This is not a held-out task evaluation and does not modify or refit the #4792 adapter.

## Result

`PASS_CONSTRUCTION` for the declared mechanics gate: 13 frozen candidate strings, 175 exhaustive prefix/terminal checks, each candidate tokenizer-roundtrips, and the constrained generation ended in one listed parseable candidate. One greedy base-model prompt was run in each arm with identical prompt and weights. Free output was valid JSON but outside the candidate set (`compactIntent=timezoneChange`); constrained output was the listed timezone set intent. The binder/simulator were not executed in this construction, so this is not an accepted action or correct task effect.

Raw timings were 1,040,935,238 ns free and 1,177,437,485 ns trie. One observation per arm is not a latency comparison. No fit, GPU, network, retry, task score, safety claim, or held-out evaluation.

## Reproduction

Use the immutable image ID, cached model snapshot, source SHA-256 and exact Docker invocation in `FREEZE.json`. `construction-result.json` is the unmodified container output. The container was CPU-only, offline, read-only except `/out`, limited to 2 CPUs / 8 GiB / 64 pids.

## Next rung

This only validates decoder mechanics. A separate fresh paired held-out allocation is required to test whether constrained decoding changes semantic intent quality with the same fitted #4792 adapter, prompt, rows, binder and simulator. Do not train again or infer safety from syntax.

