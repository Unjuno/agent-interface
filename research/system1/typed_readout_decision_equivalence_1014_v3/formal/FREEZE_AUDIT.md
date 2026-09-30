# Post-formal freeze audit note

The immutable `FORMAL_FREEZE.json` contains the SHA-256 `cfe2f32e…` computed
from the Windows worktree bytes of `SOURCE_MANIFEST.json` before staging. Git
line-ending normalization changed that manifest file's committed blob bytes;
the SHA-256 over the committed blob is
`3bfa893d8b459d0f55bf2d875c42cc94154e7cafbd3b3ee75fc5aa7e052f7abe`. The
GitHub MCP readback blob ID is `cf236ef1305d418e3be5b1b178ae143ea18580b0` and
matches the local `HEAD` Git blob.

An independent check loaded every path in the manifest from the committed Git
object database and recomputed its SHA-256. All 12 listed source/construction
files matched exactly; mismatch count was zero. These include `formal.py`,
`audit.py`, `construction.py`, `cache_ops.py`, protocol, command/environment
description, and both construction records. Each of the six critical source and
record GitHub MCP readbacks also matched the exact local Git blob ID before the
formal run.

This leaves an inaccurate standalone manifest digest field in the frozen
metadata. The frozen files and formal outputs are preserved unchanged. This
metadata discrepancy does not affect the 12 file-level source hashes or the
reconstruction audit, but is disclosed for independent review.
