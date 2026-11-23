# Chromium V5 point-mint generation guard R06

**Disposition: `PASS_SCOPED_FAKE_GENERATION_MINT_GUARD`.** The V5 point-mint
method now refuses to mint a target handle when either process or window
generation changes after the model's source observation, even when the pixel
patch is identical. The same-generation positive still mints a session alias
and keeps the private random registry ID undisclosed.

## Evidence

- Frozen base main: `759d15697be34a5db1afd6215b46ecf4e42d40d1`.
- Exact source: `research/live_control/session_v33.py`, SHA-256
  `a228cadbd1c787da021189ad4b9d823e8bed78a062fe57920db39035876fdd15`.
- Windows 10, CPython 3.11.9.
- The actual `session_v33.Backend.execute` method and actual in-memory
  `runtime.guarded_x11_v1.handles.TargetHandleStore` were called. Only the
  method's unused historical parent class was isolated during import; the
  private loader restores the prior module state before other test imports.
- Frozen negatives changed process generation alone and window generation
  alone; focus, surface, geometry, and exact textured pixel patches remained
  fixed. Both refused before registry creation.
- The positive kept both generations fixed and verified the minted session
  alias, hidden private registry key, source/fresh observation sequences, and
  equality of source/fresh patch digests.
- The R05 baseline reproduced both failures in normal and `-O`. The fix plus
  focused regression set passed **23/23 normally and 23/23 under `-O`**. Raw
  logs, exit codes, conditions, and manifests are retained in [`raw/`](raw/).

## Boundary

This closes a narrow stale-generation mint defect in the local V5 point-target
path. It is Fake-only and has no browser/X-server launch, operating-system
input, model/provider call, task effect, or live allocation. It does not show
that V5 target receipts are joined to adaptive caller v3, and it does not
establish recovery, efficiency, MAP01, Research Preview acceptance, or
reliability. The next #57 gate remains a fresh, independently admitted V5 to
v3 composed path with retained generation/capture/usage/execute/release/effect
evidence, followed by a separately frozen matched comparison. Keep #57 open.
