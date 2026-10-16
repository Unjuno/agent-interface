# A18 WSLc owner key-up bracket result

## Result

Formal candidate invocation: one. Exit 0, `PASS_CANDIDATE_SHAPE`, completed, no candidate errors. Independent raw-only auditor: `PASS_OWNER_THREAD_KEYUP_BRACKET_WSLc_SCOPED`, zero errors. Six of six audit mutation controls were rejected during construction validation.

Three explicit key-up operations produced joined caller/owner rows for W in a single-key case and W then A in a two-key case. Every owner request and XSync-return timestamp was nested within its caller bracket. Observed request-to-XSync-return intervals: 95,829 ns, 106,979 ns, and 116,762 ns (median 106,979 ns). These are X server processing brackets, not physical keyboard timing or proof of application receipt/usefulness.

The stale foreign-intent W release was rejected without a receipt or owner-row append while W and A remained down. Cancellation rejected A, asynchronously released W under its owning intent, recorded one cleanup bracket, and reached a neutral keymap. Three teardowns were verified neutral. No input authority, model call, or external effect was recorded; Xvfb and the owner thread stopped cleanly.

## Limits

This is a private Xvfb/WSLc scoped engineering result. It does not close #5156, #1907, or #59; it does not establish MAP01/human-tempo behavior, hardware key-up latency, application delivery, safety, task usefulness, game/model performance, or comparative benefit. The XSync boundary covers server processing only. Memory limits were requested but not enforced by the available kernel cgroup support. No GPU was used.

## Construction history

The first two non-formal invocations stopped before experimental events because the copied dependency directory was absent from `sys.path` (attempt 2 placed its fix after imports). Attempt 3 wrote a STOP raw before any input event because the python-xlib focus arguments were reversed; Xvfb/owner cleanup succeeded, and mutation self-test correctly declined the STOP raw. Attempt 4 had a passing candidate raw but auditor rejected an omitted A-key neutral-state field in the first teardown. Each failure/raw was preserved under `construction/`. After corrections, candidate construction and independent mutation self-test passed; formal invocation then ran once.

See `PREREGISTRATION.md`, `FREEZE.json`, `BUILD.md`, formal raw/audit outputs, and `SHA256SUMS.txt` for frozen conditions and evidence.
