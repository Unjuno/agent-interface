# WSLc current-runtime varied-value Calc pair

Fresh fixed-order exploratory pair on Calc: em01 compiled then em02 fresh, 472/615 instead of the earlier 641/283 workload. Both use one persistent model session per arm, gpt-6.1-sol requested low, private Xvfb, WSLc 1 CPU / 1 GiB and no container network; host model calls are separate. The initial pixel reference is deliberately from the older values to trigger the compiled yield. Both methods use expected-value OCR and scripted Save; this is not temporary-obstruction or partial-input recovery.

| allocation | route | task interval | launcher | calls | input (cached subset) | output | effect |
|---|---|---:|---:|---:|---:|---:|---|
| em01 | compiled | 6.481 s | 11.562 s | 1 | 12,185 (8,192) | 62 | exact 472/615 |
| em02 | fresh | 10.578 s | 12.938 s | 2 | 25,751 (12,160) | 156 | exact 472/615 |

The compiled method yielded SAFE_YIELD / effect_unavailable after one completed transition, then a fresh observation and OCR led to a separately guarded Save without entry replay. Both saved FODS files independently parse to exactly the two expected numeric cells with no formulas, both owner closes report verified release, and final key/button readback is neutral. The local audit also checks input hashes, model request/image/response associations, call accounting, and action release receipts. Extract raw.zip beside audit.py and run python audit.py without optimization. Raw captures, receipts, OCR records, candidate scripts, conditions and saved FODS are retained; private model protocol journals are not included.

The source snapshot's non-test Python files in the backends, CLI, core and guarded X11 packages match main be0cae0a635e5852924a12c8ae971044cc0ce276; eight named model-client/schema files also match. The research runner adds a deadline check after OCR and before accepting the recovery cue/minting. The 1 GiB limit excludes swap according to WSLc's warning. Task interval excludes startup/preparation/final audit; cached input is included in input. The launcher interval includes process startup but excludes source preparation and audit.

One ordered pair with different provider/cache states, route internals, scripted save and a fixed expected-value OCR cue cannot establish a population speedup, cost, broad reliability, arbitrary values, persistent obstruction or partial-input recovery. The fresh arm has an extra model call by design. This does not establish MAP01 completion or a third-arm comparison.
