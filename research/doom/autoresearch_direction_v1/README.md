# Autoresearch direction and freshness lane

Read REPORT.md for the 33 real-container comparisons and remaining defects. Sources were executed against the immutable 9e6d5ecd runtime bundle, not the moving publication main.

## Offline replay

The full raw bundle named and SHA-256-bound by archive.json is a conversation attachment, NOT uploaded to GitHub or Actions. Extract it into a NEW standalone directory. It contains full plans, failed preflight, raw case logs, images, fixture saves and the recorded runtime source closure.

From its `autoresearch_direction` directory:

```sh
python research/doom/autoresearch_direction_v1/audit.py . --out replay.json
python research/doom/autoresearch_direction_v1/test_runner.py
python research/doom/autoresearch_direction_v1/test_audit.py
```

Pillow is required for pixel checks; `--no-pixels` only replays metadata. The tests require retained preflight/case evidence, not just a repository checkout. Both valid outcomes and 33 inherited invalid final acquisition brackets are reported. An audit PASS does not erase those defects.

## Fresh experiments

Never rerun consumed allocation IDs. The runner's directory layout assumes an isolated experiment workspace with the full pinned source bundle in its `runtime/` directory. DO NOT unpack it over the product `runtime/` of an ordinary repository checkout. Reconstruct dependencies, create new outputs, relocate fixture paths, and freeze a new plan before fresh execution. The raw replay archive contains only the 26 recorded source dependencies, not a full ViZDoom distribution.

These candidates do not grant policy authority from scorer data. `advance_action(1, True)` is an explicit measured evaluator intervention, not proof of zero perturbation or a generally applicable provider refresh method.
