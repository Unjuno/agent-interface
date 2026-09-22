# Retained compare/Undo reentrancy evidence (#4090)

Scientific decision: **PASS_COMPARE_UNDO_REENTRANCY_BOUNDARY_SCOPED**.

This is retrospective evidence delivery of the already-consumed local allocation `undo-compare-commit-20260922-01`; it is **not GitHub preregistration** and this publication performs no GUI/formal rerun. The original experiment had 40 fresh Tk sessions in two frozen 20-case batches: 20 correct target Undo, 8 wrong Undo comparator outcomes, and 12 unresolved refusals. Comparator failures remain failures and refusal is not compensation success.

The eight ordered `ORIGINAL_ADDITIVE.patch.part*` files concatenate to the exact conversation-retained additive patch SHA-256 `0ffb13daef7ee750f2e9a08f8373676480089b660014f611d10e1e896ca1218a` (3,435,818 bytes, 69,683 lines). Applying that patch to a clean tree creates all **302 original study files / 3,279,608 bytes** under `research/integration/undo_compare_commit_v1/`, including complete sources, formal raw records, excluded construction, process exits, freeze, audit and corruption controls. The old historically true write-unavailable notes remain inside those original bytes.

Read `PACK.json` before reconstruction. `reconstruct.py` validates every part and the combined patch before writing it; it does not execute the experiment.

Read-only reconstruction on a clean checkout:

```sh
python -B research/integration/undo_compare_commit_v1/reconstruct.py /tmp/undo-compare.patch
git apply --check /tmp/undo-compare.patch
git apply /tmp/undo-compare.patch
python -B research/integration/undo_compare_commit_v1/verify_bundle.py --out /tmp/undo-compare-readonly-check
```

Use fresh destinations. **Do not run the consumed formal launchers.**

Scoped integration constraint: current history/scope validation must remain valid through the compensation effect. A nominally single callback is insufficient if it pumps the event loop between check and Undo. This is cooperative Tk/X11 evidence, not production-runtime promotion, a generic GUI transaction, model utility, latency benefit, or global-roadmap completion.
