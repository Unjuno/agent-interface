# Issue #5139 current-main support-balance preparation

This bundle is an additive successor to #5014 on current main `eddcf7a47c1f3c47165288037e66f66da0c3138a`. It regenerates the support and held-out pools with three fresh seeds, uses the current-main protocol, and carries an independent stdlib dataset/output auditor.

Current disposition: `STOP_QUEUE_SLOT_UNAVAILABLE`. The #5085 queue assigns the shared Docker lane to #5134. This bundle records **zero** container invocations, model loads, CUDA calls, fits, and raw outputs. The 16 GiB RTX 3080 was observed idle, but that is not a lease. Do not start Docker, load the model, or call CUDA from this allocation. A later #5139 execution needs a separate exact lease and a new freeze against then-current main.

Run host-only construction checks with:

```powershell
python -m pytest -q research/experiments/qwen05b_abstention_balance_5139_v1
```

`formal-dataset.json` is the byte-frozen generated input. `FREEZE.json`, `FREEZE.sha256`, and `SHA256SUMS.txt` bind source, input, model/tokenizer files, and the cached image digest. `PREREGISTRATION.md` gives H/T/D/C/U; `STOP_RECORD.json` captures the queue disposition. The pinned-image CPU construction and preflight remain unrun because the shared Docker slot is assigned elsewhere.
