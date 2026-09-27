# Recovery review: Issue #3952 split-tail allocation

The original branch
`research/inbox-split-tail-20260922` contains a complete, lossless source
capsule and freeze for allocation `inbox-split-tail-3952-20260922-01`, but no
formal journal or launcher exit receipt. The capsule was restored to a fresh
temporary directory using the published `restore.py`: all 16 files restored,
and the tool explicitly reported that no experiment was executed. The
restored auditor's 12 synthetic tests passed locally. These tests exercise
only constructed fixtures and mutation controls; they do not audit the
reported formal output.

## Formal outcome boundary

Issue [#3952](https://github.com/Unjuno/agent-interface/issues/3952),
comment [5766411966](https://github.com/Unjuno/agent-interface/issues/3952#issuecomment-5766411966),
reports a 178-row journal for 22 streams and 88 reader calls, plus semantic
reconstruction and rejection of all 10 corruption controls. It explicitly
does **not** report a formal PASS: the overall disposition is
`HOLD_SUPERVISOR_EXIT_UNOBSERVED`. The timed-out outer execution did not
persist `execution.json`; top-level runner exit codes are unknown. The full
frozen auditor was invoked once and failed with `FileNotFoundError` for that
missing receipt. Its failure is not repaired or relabelled here.

The Issue reports raw SHA-256
`368bd08431d9c95f8b9148fee9d82b9169ab504430699c5a620bb1a08a7fe2cb` and a
103.230923015-second journal, but neither raw journal nor output receipt was
found in the remote branch, source capsule, or bounded local search. The
reported hash and semantic reconstruction therefore remain Issue-reported;
they were not independently read back from raw bytes in this recovery.

## Scope

The original single allocation is consumed. No writer/reader launch, retry,
resume, replacement, or formal rerun was performed. The source capsule and
synthetic auditor test result are preserved, but they do not substitute for
the missing raw journal or OS-level exit receipt. No performance, task-effect,
GUI, provider/model, ACK, or production-readiness conclusion follows. Any
further supervisor/timeout validation requires a separately frozen successor.
