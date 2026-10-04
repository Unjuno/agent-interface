# MAP01 scorer-tail receipt construction A01

This bounded offline construction asks whether the new scorer-tail receipt validator accepts authentic per-key key-up receipts from the six retained cells in `absolute_pair_59_4d74_20261004`.

- **H:** Each retained `d` key-up receipt contains the exact verified owner, empty-after-batch, and explicit key-up fields required by the tail helper.
- **T:** Read the six frozen `runtime/events.jsonl` Git blobs, select one `input_release_transition` for key `d` per cell, and call the exact adapter with `max_duration_ns=0`. The sampling callback raises if invoked.
- **D:** Accept only if all six retained receipts pass validation, all return `CENSORED/deadline`, and no scorer callback runs.
- **C:** This isolates receipt-shape compatibility; it does not measure any time after release or join a running controller.
- **U:** The offline test uses local Git objects and a zero-duration fake clock. It establishes neither scorer timing nor live V39/V12 integration, game response, task effect, recovery, or MAP01 completion.

Reproduce from the repository root:

```powershell
python research/doom/scorer_tail_receipt_construction_a01_20261005/run.py
python research/doom/scorer_tail_receipt_construction_a01_20261005/audit.py
git diff --check
```

`FREEZE.json` pins the helper, direct dependencies, and six input event blobs. `RESULT.json` retains only the cell/step/key identity and bounded outcome; owner IDs and intent tokens are not copied. `AUDIT.json` independently checks the pinned objects, one real `d` receipt per cell, and zero-sample accounting.
