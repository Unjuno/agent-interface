# Inspection success is not a failed MCP tool execution

The primary Calc pair exposed a successful target inspection with an image and valid candidate request that nevertheless set MCP isError=true. Its body correctly said needs_review. The pair's first verifier consequently mistook expected pending review for execution failure. The historical bundle is preserved unchanged.

The integrated server now returns isError=false for successful inspect_target evidence/candidate delivery. status=needs_review, input_dispatched=false and authority_granted=false remain. Explicit target review, rechecking, expiry, binding revision and recovery rules are unchanged. A requested image must actually be available in presentation. Errors, capture/recheck failures, image-presentation failures, persistence failures and failed target review retain isError=true. This is a transport distinction, not an authority or task-completion signal.

Before the fix, a seven-case regression test failed in precisely its two valid inspection cases (metadata-only and image). Afterward, 22 persistent-session tests pass, including invalid repeated review and five failure controls. Full native checks pass: 281 protocol and 126 harness tests.

Primary use of a newly built portable archive at source 39e7d6d3997fbfa2ebac85261a012c214a7de989:
1. Inspect a fresh Calc main window with an image: isError=false, needs_review, revision 1.
2. After actually viewing the image, deliberately submit a mismatched review ID: isError=true, error detail, same revision/target, no input.
3. Close: isError=false, no input release needed, relay exit 0.

This three-call probe is not a task-performance trial. Fixture teardown codes Xvfb/Openbox/LibreOffice 0/1/255 are cleanup outcomes, not graceful application-exit claims. No task input, default wait change, sensor, helper model, latency or token claim is included.

Run `python3 -O runtime/results/inspection-error-flag-01/verify.py` to check all 39 retained files, raw MCP flags, review/image identities, unchanged target/revision, exact source in the tested archive, prior failing tests and passing checks. Historical experiment/verifier files were not rewritten.

The design follows the MCP distinction between a tool's successful output and [tool execution errors](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling). Here pending review is the expected output of the inspection tool. It must still be acted on explicitly by the caller.
