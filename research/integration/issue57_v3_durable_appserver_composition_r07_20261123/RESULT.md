# Issue #57 R07: interrupted terminal after observed usage

## Result

On current main f64c58179524db4be64b116a265182c9facc1736, one synthetic JSONL peer emitted thread/tokenUsage/updated and then terminated the turn with status interrupted. The real client/parser, grounding model, v3 adapter/caller, durable Calc allocation writer, and registered ProspectiveRun custodian retained exact turn/thread IDs and all five observed usage counters. The caller recorded one failed attempt and zero completed calls; no execution/effect receipts were created; projection/run remained HOLD and dispatch remained disabled.

Windows CPython 3.13.14 focused case: 1/1 normal and -O. Full transport module: 11/11 normal and -O. A preliminary -O runner invocation had an argument-order error (No module named -O) and never started tests; its raw output is preserved as preliminary_harness_order_error_*. The runner was corrected and the qualified -O runs passed.

This is synthetic terminal-custody coverage, not external-provider behavior, live GUI/task effect, efficiency, or reliability evidence.

## Reproduction and custody

Frozen conditions, runner commands, stdout/stderr bytes, exit codes, preliminary harness failure, result summary, and SHA-256 manifest are retained in this directory.
