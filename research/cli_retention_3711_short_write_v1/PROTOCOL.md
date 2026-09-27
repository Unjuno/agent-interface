# #3711 short-write construction protocol v1

Status: preregistered; no result claimed yet.

## H / T / D / C / U

**H — hypothesis.** `runtime.cli_v1.__main__._emit` currently ignores the character count returned by `sys.stdout.write`. A writer that accepts only a prefix and returns normally can therefore make the CLI report ordinary success although the JSON response was truncated. One emission attempt should fail explicitly on a short write, without retrying delivery; the pre-persisted raw report must remain recoverable and the dispatch must not be repeated.

**T — target.** On additive branch `research/cli-short-write-3711-v1`, use frozen main source blobs `__main__.py` SHA `871600960dfb4404f3455d2df6b3d8686cf0cac9`, `test_attempt.py` SHA `cbc9d0c17ca3a4391593dcea00901083ceacffcb`, and `attempt.py` SHA `de8041869d216014afe3322379fa2ce080367411`. Add one deterministic test using a stdout stub that returns a short character count. Run public CLI dispatch with a retained run-directory and a fixed synthetic receipt; assert one stdout write, one dispatch, an explicit write failure, and byte-identical request/report files after failure. Correct `_emit` to detect the short write and flush once, without retrying output. Validate via the existing Runtime unified CLI v1 workflow across Ubuntu, Windows, and macOS. No GUI, model, native input, network, or live application.

**D — decision.** Construction PASS only if the focused test and complete workflow are green on all three OSes, the short writer is called once, dispatch is called once, the report JSON matches the fixed synthetic receipt, and request/report bytes remain unchanged after output failure. FAIL if the CLI silently succeeds or dispatch/output is retried, if the report is missing/changed, or if any required assertion fails. HOLD while any required CI job is queued or incomplete. Infrastructure STOP if the workflow cannot run; do not translate it into test FAIL/PASS.

**C — constraints.** This is a mocked short-write construction test, not an induced OS pipe truncation or real consumer disconnect. The actual OS closed-pipe case is separately covered by merged PR #3723. Current local C: free space is 0 bytes and the Docker Desktop Linux engine pipe is absent, so do not execute locally, start/repair Docker, pull images, or clean storage. GitHub Actions is the planned remote verification surface and is not evidence of this PC's local Docker gate.

**U — limits.** A passing result establishes only detection of a normally returning short write in the tested CLI path on the listed CI OSes and preservation of one synthetic attempt. It does not establish power-loss durability, OS-level partial pipe delivery, recovery UI/status for request-only interruptions, live action behavior, performance, or broad reliability. Keep #3711 open for its other remaining gates.
