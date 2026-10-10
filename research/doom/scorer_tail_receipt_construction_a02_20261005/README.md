# MAP01 scorer-tail receipt construction A02

This second offline construction checks the strict V2 identity layer against the six retained per-key `d` releases in `absolute_pair_59_4d74_20261004`.

- **H:** The retained six receipts satisfy the stricter nonempty program/step/key/owner/token contract, with the nested owner key-up matching all those fields; malformed identity mutations fail closed.
- **T:** Read the six frozen event Git blobs, validate their raw `d` receipts with the exact V2 tail adapter using a zero-nanosecond budget, and test four negative identity mutations.
- **D:** Accept only if two releases are present in each pulse cell, none in coast cells, all six real receipts pass strict validation, all return censored/deadline with zero samples, and all four mutations are rejected.
- **C:** This tests the identity boundary and retained data compatibility. It does not measure a positive-duration tail, V39 runtime behavior, or in-game effect.
- **U:** Offline Windows CPython construction against local Git objects and a fixed clock. No live V39 session, model, GUI, OS input, formal allocation, task effect, recovery result, or MAP01 exit.

Reproduce from the repository root:

```powershell
python research/doom/scorer_tail_receipt_construction_a02_20261005/run.py
python research/doom/scorer_tail_receipt_construction_a02_20261005/audit.py
git diff --check
```

`FREEZE.json` pins the V2 validator, V1 sampling implementation, direct polling dependencies, and all six event blobs. The result retains only cell/step/key and bounded outcomes; owner IDs and intent tokens remain in the original pinned Git objects.
