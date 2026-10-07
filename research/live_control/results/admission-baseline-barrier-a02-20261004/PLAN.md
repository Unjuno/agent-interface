# Admission-baseline callback failure repair — A02

## H / T / D / C / U

- **H:** The accepted-sink failure repair at exact PR #7429 head `e22e59732033438916415f71b53f86695b1c448a` preserves fail-closed admission uncertainty, prevents backend execution, and lets shutdown safely avoid joining an unstarted worker in both ExecutorV12 and the ExecutorV13 wrapper.
- **T:** One deterministic host-Python candidate invokes each exact frozen executor once with a fake backend and an injected `RuntimeError` from the accepted-event callback (standing in for scorer-baseline failure before admission publication). It captures executor state before and after `close()`.
- **D:** Source files are immutable snapshots from the exact PR head. Synchronization uses the real `submit()` call path, not timing estimates. No baseline success path is included; A01 tested the ordering seam.
- **C:** For both executor versions, no backend step may run; the active slot, one-shot ID and lease must remain fail-closed; the error must be typed as `delivery_unknown`; worker identity must remain unset; `close()` must return without a join-before-start exception. ExecutorV13 must remove its not-started release watcher registration.
- **U:** This checks only a fake accepted-event callback failure with no game/scorer/input. It does not check a real callback that samples VizDoom, the separate V13 release-sink failure found in review, live recovery, task effect, or cleanup/re-admission semantics beyond shutdown.

## Frozen inputs and execution boundary

- Base `main` at freeze: `0178fd24e9c317fff40e0fa1952fbe7e8ae01078` (the PR #7469 merge containing an independent archived accepted-sink reference check).
- Candidate source stack: exact PR #7429 head above; source closure is under `source_snapshot/live_control/` and is hashed in `SHA256SUMS.txt`.
- Candidate: `python3 candidate.py`, one execution covering one V12 and one V13 fake-backend cell.
- Audit: `python3 audit.py`, saved-record only.
- Host Python on macOS; OrbStack was not retried after the prior daemon content-store preflight failure. No external process or shared resource is used.
- No candidate retries.
