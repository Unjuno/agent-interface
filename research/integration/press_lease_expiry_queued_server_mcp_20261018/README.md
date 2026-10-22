# Queued press crossing the guarded lease deadline — MCP/Fake X

Date: 2026-10-18. This is a local finite construction regression on ordinary Ubuntu WSL2 (Python 3.12.3), not a WSLc allocation. It uses the standard `runtime.cli_v1` MCP server/caller and the existing Fake X transport harness. No Docker, live X server, physical input, model, or formal allocation was used.

## Question and frozen boundary

If the selected MCP caller's CTRL-down request is already queued for Fake X server processing when the original five-second guarded input lease expires, what happens while the server is stalled, after it resumes, and on a caller-initiated retry using the same still-live alias?

The test starts the harness clock at 1,000,000 ns, lets the original caller queue CTRL down, holds the server-processing barrier, advances the same monotonic clock to `bridge.deadline + 1`, and checks state before releasing the barrier. The barrier is finite and explicitly released by the test; this does not model a permanently wedged platform call.

## First observed result and correction

The first targeted run exposed a caller policy gap. Before the fix, the original expired call ended `execution_failed` and Fake X reported cleanup release verified, but a second explicit call using the same alias returned `completed`; its response still said `replay_allowed=false`, and the owner had not set `review_required`. Thus the no-replay field was advisory for a new caller invocation and did not enforce a fresh review after a terminal partial-input failure. The first failure was emitted by the tool but was not redirected to a file; this paragraph is a preserved observation, not a byte-identical raw transcript.

The caller now sets `bridge.review_required` when guarded input returns `execution_failed`. The focused regression checks this only after the original call reaches its terminal result, then confirms the same-alias retry is refused with no added emissions. This requires a fresh visual review before further input; it does not certify the task effect.

## Retained final result

While the barrier is held, the original MCP call remains pending, release is not confirmed, calls that need the single owner are busy, the server queue contains one session-writer CTRL-down, Fake X has not yet applied it, and the release ledger still owns CTRL. After the barrier resumes past the deadline, Fake X applies that already-queued CTRL-down; the next key (`a`) is refused by the expired lease; the same writer sends CTRL-up. The original call ends `execution_failed`, cleanup is verified by Fake X, physical-down state and the ledger are empty, and a second call with the old alias is refused because review is required.

This establishes that the deadline does not retract an input request already queued below the caller. It does not establish a wall-clock release bound while X I/O/server processing remains blocked: this fixture deliberately resumes. It also does not establish native X ordering, physical release, independent task success, recovery efficacy, or matched efficiency.

## Verification and source identity

Base: main commit `71f89473b4ce69788066cabe7cd33b992f1a49e4` (the repository documentation-only plan update is included). The source changes in this worktree are local and are hashed below.

Command in each mode:

```text
python -m unittest runtime.cli_v1.test_mcp_transport_cancellation
python -O -m unittest runtime.cli_v1.test_mcp_transport_cancellation
```

Results: **7/7 passed** in normal mode and **7/7 passed** with optimization. The related guarded MCP, guarded recovery, interruption receipt, and transport cancellation modules also pass **60/60** in both modes. Exact stdout/stderr files are `normal.txt`, `optimized.txt`, `related-normal.txt`, and `related-optimized.txt`. The earlier `first-module-assertion-timing-FAIL.txt` preserves an intermediate harness mistake: a review-required assertion was initially placed in the pre-resume snapshot, before the failed terminal result existed. That failed check is not evidence of a product failure and remains retained without relabeling.

SHA-256 (source files as tested):

- `runtime/cli_v1/mcp_guarded.py`: `e31fe8d0ee7850551eb866370a8e82975ba03f334a572002f7d9fe4e334a9cd1`
- `runtime/cli_v1/test_mcp_transport_cancellation.py`: `9a95ba4d12ec69c079f4b26e08cc4595c144d345cbb94d2e0fbf06b0e239a5a3`
- `normal.txt`: `b8b03da3aef01045051063d51c6119ed051cb56c3e09c4fab5682d82f2ba0312`
- `optimized.txt`: `15977c9b170b09f26722b1e672d7d0736f768f8a3cb47c1d2e6cb606c2092721`
- `related-normal.txt`: `eddf78970ddaccac14e3b2ac200c2e2814afc2e95df64b7578e25e307a30edca`
- `related-optimized.txt`: `86c29a114c097dd9ab176ed9e90eb97d9e695e10647a3a4e25bb8326486a1e6c`
- `first-module-assertion-timing-FAIL.txt`: `30a8ba719eee064228a3559d1f2f17a9fe468c360a6e2e0f7204e86b46028935`

The output subtree has a narrow `-text -whitespace -filter -ident` attribute so Git preserves the captured log bytes.

## Next discriminating work

Connect single-authority writer retirement/fencing and late-send rejection through this same selected caller. Preserve the observed post-deadline queued press as a counterexample; do not claim a bounded physical release unless a test proves that bound under nonresponse. Native X behavior still needs an eligible, freshly authorized environment and unused allocation.
