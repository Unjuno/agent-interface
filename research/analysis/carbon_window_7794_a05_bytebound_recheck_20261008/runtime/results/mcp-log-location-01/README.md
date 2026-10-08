# Fixture event-log placement: retained integration diagnostic

Two fresh, sequential WSL/Xvfb allocations used the same public MCP program:
click the entry, type `log-location-check`, Ctrl+S, fixed 50 ms wait, capture,
and release. Each then reread the retained call with `interface_results`.
The sole intended condition change was fixture event-log placement: mounted
Windows evidence directory versus Linux temporary storage copied after shutdown.
Both effect files saved the exact marker and both release receipts verified.
Primary visual inspection found a blank/unsaved returned image in the mounted
condition and the correct text/saved label in the Linux condition.

This supports treating synchronous mounted logging as a possible confounder,
not increasing the production fixed-wait default on this evidence. It does not
prove causation: one sample per condition, fixed mounted-then-Linux order, no
callback timestamps, and no matched model/task timing or formal container audit.
The calls were scripted; primary inspection occurred after execution. There was
no additional input replay. No sensor or production runtime was changed.

The archive preserves both complete local allocations and their original hash
manifests. `RESULT.json` pins the archive hash and records the checkout revision
checked after execution. Source was not independently attested at process launch.
Both owners exited 0; tracked fixture and Xvfb exits were -15 and 0. Descendant
verification remains false. Prior stale-image trials are unchanged.

Related: Issue #3370; public result retrieval #3576/#3580. This is draft diagnostic
evidence, not a release gate or a general responsiveness claim. Verify archived
bytes with `python runtime/results/mcp-log-location-01/verify.py`; the verifier
reads archive members without extracting files or executing archived programs.
