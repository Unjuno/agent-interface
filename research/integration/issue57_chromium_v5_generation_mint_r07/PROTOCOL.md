# Chromium V5 point-mint generation guard R07

This is a post-merge current-main recheck after PR #10516 entered main. One
normal and one `-O` run execute the same 23-test generation-mint, semantic
handle, compiled-caller handoff, and adaptive caller/core bundle against the
frozen main SHA in `conditions.json`.

The run validates that the merged tree contains the guard and retains the
same two-generation-change negatives plus same-generation positive. No browser,
X server, operating-system input, external model/provider, or live allocation
is used. R07 is a new post-merge check, not a retry of R06 or the pre-merge
baseline. Any failure is retained and not repeated under this run ID.
