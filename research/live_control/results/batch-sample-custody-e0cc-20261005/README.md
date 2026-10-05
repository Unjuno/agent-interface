# Original batch-sample custody

See [RESULT.md](RESULT.md) for the reproduced defect, actual-owner fake-X tests, limits and audit correction history.
This evidence directory contains only inert data/source snapshots; no candidate runs on import or test discovery.

Ordinary regressions from a checkout containing the production/test patch:

```bash
PYTHONPATH=research/live_control:research/doom:research/observation_gating python3 -B -m unittest -v test_input_owner_v12_batch_sample_custody
PYTHONPATH=research/live_control:research/doom:research/observation_gating python3 -B -m unittest -v test_input_owner_v12_explicit_up_cancel
```

Use the repository's Python 3.12 environment. Xlib is replaced with an in-process fake server; current owner threads are started and closed. No real X server, GUI/game, model or native input is used. The new test uses synthetic monotonic labels, not measured latency. This is an ordinary regression, not replay of a consumed formal allocation.

`base-source-manifest.json` pins 56 existing files from main `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`. Each run pins 57 exported source files including the new test. All original Git source blobs remain reconstructible from that ancestor of main. Before/after owner and test snapshots are inert `.py.txt` evidence.

Private raw remains unchanged. Public copies normalize only private work/runtime prefixes. Receipt hashes bind private originals; `public-custody.json` binds each original/public pair and `publication-manifest.json` verifies public bytes. Trace JSON and scientific results are retained. Audit source snapshots describe private readback and are not portable replay entry points.

The independent review is technical evidence, not a FINAL-v5 content-quorum or exact-current-main integration vote.
