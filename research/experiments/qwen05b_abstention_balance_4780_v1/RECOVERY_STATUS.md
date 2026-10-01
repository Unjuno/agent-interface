# Recovery status — Issue #4988 original branch package

The full 23-file source package from remote branch
`research/qwen05b-abstention-balance-4780-20260928` is preserved verbatim under
[`recovery/original_branch_tip_20260928/`](recovery/original_branch_tip_20260928/).
The existing main-root `README.md` and `STOP.md` are not overwritten; the
original branch versions are inside that recovery snapshot.

The immutable one-shot allocation `qwen05b-abstention-balance-4780-20260928-01`
stopped in runner preflight because it read `formal_input_sha256` at the wrong
JSON level. Formal seed fits = 0, model load = 0, and retries = 0. This is a
runner/schema STOP, not a model result. Merged PRs #5016 and #5030 separately
retain STOP explanation and complete host-capture corrections; this archive
does not supersede or alter them. The original branch's linked host-log path
was not present in its 23-file subtree and is not fabricated here.

Recovery was read-only with respect to the experiment: no model, GPU, Docker,
runner, auditor, training, or evaluation was executed.
