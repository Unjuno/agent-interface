# Issue #59 A02 — OS-backed scorer-tail readiness under callback overrun

This construction exercises PR #7692's frozen `MainThreadScorerStdin.sample_tail` against a real Windows socketpair, the source's real `select.select` readiness helper, and `time.perf_counter_ns`. A 1 ms scorer-call control with the command already ready returned `command_ready` after one sample and one poll. With a 25 ms synchronous scorer call and a 10 ms period, both a command ready at entry and a command written to the socket 5 ms into the first scorer callback remained unread while the tail made four samples, performed zero readiness polls, and ended at `deadline_overrun` after about 101 ms.

The independent audit applies the preregistered behavioral gate and passes 6/6 substantive checks; four mutation tests pass. It also identifies a candidate classification defect: the candidate only recognizes `deadline`, while this real-clock run correctly terminates as `deadline_overrun`, so `RESULT_V3.json` says `INCONCLUSIVE_OR_DIFFERENT_SOURCE_BEHAVIOR` despite meeting the frozen failure criterion. The raw is not edited; see `AUDIT.json` and the run history.

## Evidence order

- `RESULT.json`: first completed but invalid-clock construction; retained unchanged, zero samples, excluded from interpretation.
- `RESULT_V2.json`: exploratory run before a valid freeze; behavior matched A01 but excluded from the preregistered disposition.
- `RESULT_V3.json`: one candidate invocation after `FREEZE.json`; source-pinned, real socket readiness and monotonic time.
- `AUDIT.json`: separate reconstruction from the frozen decision gate and output, including the candidate-label mismatch.
- `RUN.md`: the first three construction stops, clock mismatch, exploratory run, and final frozen invocation.
- `SHA256SUMS`: package integrity list.

## Scope

This is a source-boundary construction only. A socketpair provides actual OS descriptor readiness, but it is not stdin, a DoomGame thread, a GUI, keyboard input, model, live game, or safety trial. The command payload is inspected using `MSG_PEEK` after the tail, so no command is consumed. It establishes no task effect, usefulness, latency distribution, recovery benefit, survival, or MAP01 outcome.

## H/T/D/C/U

- **H:** In the pinned adapter, command readiness can starve behind repeated synchronous scorer callbacks when each callback overruns the sample period.
- **T:** One fast control and two overrun cases using the real socket readiness helper and monotonic clock; 10 ms sample period, 100 ms tail deadline, 25 ms overrun callback; one candidate invocation.
- **D:** FAIL if the fast ready control returns `command_ready`, and both overrun cases keep their command bytes unread, receive zero readiness polls, run at least three samples, and terminate at/after the deadline. Otherwise retain an uncertain/hold result.
- **C:** The socketpair controls readiness directly. It does not model console pipes, arbitrary Windows selectors, OS scheduling distributions, command dispatch, or the full runner.
- **U:** Single host and call per case; no timing distribution or production-effect claim. The currently checked PR head equals the frozen commit, but future revisions may differ.

## Reproduction

Run `python audit.py` and `python -m unittest -v test_audit.py`. The original one-shot candidate raw is already retained; do not rerun `candidate.py` as part of auditing.
