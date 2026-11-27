# Xvfb blocked-release fallback failure — run 39666986655

**Disposition: one failed non-prestarted invocation; release UNKNOWN.** This record preserves the failing Actions log excerpt captured from the X11 integration job. It is not a successful release trial or a reliability estimate.

## Provenance and conditions

- GitHub Actions run: [39666986655](https://github.com/Unjuno/agent-interface/actions/runs/39666986655), workflow `Runtime X11 v1 Integration`, job `x11-integration` (`119454518333`).
- PR head: `a3e0d352522c0ccada367e586bf1be81f0e4c4a0`; the only code change in that PR was a synthetic caller-composition test.
- Private Xvfb workflow; the `AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR` switch was unset for this legacy invocation, so the default non-prestarted cleanup worker path ran.
- The retained log is the output of `gh run view 39666986655 --log-failed`, saved as UTF-8 without a BOM. SHA-256 is recorded in this directory's `SHA256SUMS` and the experiment root manifest.

## Observed failure

The standard caller retired the blocked owner and observed a different XRes PID at the same resource base. The cleanup worker then failed to complete cleanly: its recorded exit code was `-15`, elapsed time was `669.189222 ms`, and no release result/readback was returned. The caller kept `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`, and `late_server_request_possible=true`. The test expected `owner_release_attempt.status=readback_verified` and failed that assertion.

Other invocations in the same workflow later passed, including the dedicated opt-in `prestarted-cancel-xvfb` job. The workflow wrote repeated executions to the same artifact path; the downloadable JSON is the later successful result, not the failing attempt. The log therefore preserves the failed assertion and embedded receipt, but the original failed invocation's standalone JSON was not retained by the workflow. Do not treat the later artifact as replacing this failure.

## Limits and next discriminator

This is one schedule on one private Xvfb, with an intermittent result. It does not identify why the fallback cleanup worker was terminated, prove that the test-only change caused the failure, or support release reliability. The prestarted worker path has a distinct passing packet. Keep the fallback outcome UNKNOWN until the deadline budget and cleanup-worker termination boundary are isolated and repeated on fresh runs with per-attempt artifact names.
