# Fail-closed per-key owner selection

See [RESULT.md](RESULT.md) for exact source scope, four-route regression outcomes and limits.
The production and test changes are in the parent `research/doom` directory.
This evidence directory contains only inert data/source snapshots; it is not an import or test entry point.

Ordinary regression replay from a checkout containing this patch:

```bash
python3 -B research/doom/test_perkey_owner_source_guard.py -v
```

This requires the existing Python 3.12 research dependencies (including NumPy/Pillow), but no native Xlib, vizdoom, game or display. The test supplies inert native modules and intercepts session construction. All four subprocesses have a 20-second timeout. This command is a regression, not a replay of a consumed formal allocation.

Receipt hashes refer to the original private logs. Public copies normalize only the private work/runtime prefixes; `public-custody.json` binds each original/public pair. Public byte integrity is checked by `publication-manifest.json`. The original logs remain unchanged. Audit source snapshots are inert and describe their original private readback; they are not portable replay scripts.

The source closure is reconstructible from Git parent `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`, `base-source-manifest.json`, and the production/test patch. Per-run manifests retain the executed source identities. First failures are retained; no log was removed to obtain PASS.
