# Four-way malformed reason mutation matrix

Date: 2026-09-29 (Asia/Tokyo)

## H / T / D / C / U

- **H — Hypothesis:** the candidate auditor's non-string reason guard rejects JSON arrays/objects for both `yield` and `no_action` in both support and heldout pools, without an uncaught exception.
- **T — Test:** on the synchronized #5208 candidate (main `d8ca8bfed9cd8d84201c91645e4ed25364181d3f`), mutate four rows: support/yield/list, support/no_action/object, heldout/yield/object, heldout/no_action/list. Synthetic sentinels formal `830513931`, support `830513932`. Run the independent auditor; no model, GPU, CUDA, Docker, GUI, or formal allocation.
- **D — Data:** all four rows produced explicit `support_class_mismatch` / `heldout_class_mismatch` errors, two per pool, with `raised=null`. Input SHA-256: `1cce1c6e42425ed54524e67a554c57ba8e937287ec2405679f2061ac0818fbfe`. Machine output: `result.json`. Full package suite: **31/31 passed**.
- **C — Conclusion:** the candidate fix handles all four operation × pool × JSON-type combinations recorded in the parallel evidence-only PR #5223, whose frozen pre-fix candidate reported 4/4 uncaught `TypeError`s and whose local diagnostic guard rejected all four. Our branch's independent implementation now has a committed regression test covering those four cases; no parallel branch or historical result was altered.
- **U — Limits:** fixed synthetic mutations only; not a complete JSON parser fuzzing campaign, Qwen quality result, GPU performance test, or permission to run the model. #5139's GPU/Docker gates remain outstanding.

## Reproduction

From the experiment package directory, with `PYTHONPATH=.`:

```powershell
python evidence/malformed-reason-matrix-20260929/reproduce.py
python -m unittest discover -s . -p 'test_*.py' -q
```
